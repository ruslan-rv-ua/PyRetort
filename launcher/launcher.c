/*
 * PyRetort launcher: starts the bundled Python without cmd.exe.
 *
 * generate_exe (src/pyretort/builder/exe_generator/generate_exe.py) copies
 * this executable next to the application and writes the command to run into
 * `command_template` below. At run time the launcher:
 *
 *   1. reads the command out of `command_template`;
 *   2. replaces every `{EXE_DIR}` in it with the directory the launcher is in
 *      (no trailing backslash);
 *   3. appends a space and the raw tail of its own command line, so that the
 *      arguments reach the child exactly as the caller wrote them;
 *   4. starts the result with CreateProcessW, puts the child into a job object
 *      that dies with the launcher, waits for it and exits with its exit code.
 *
 * Placeholder format. `command_template` holds COMMAND_CAPACITY UTF-16 code
 * units. In the compiled template it contains the marker
 * PYRETORT-LAUNCHER-COMMAND-PLACEHOLDER followed by zeros, and the marker
 * occurs exactly once in the file. generate_exe overwrites the whole region
 * with the command encoded as UTF-16LE and padded with zeros, so a command is
 * at most COMMAND_CAPACITY - 1 units long. The array is `volatile` so that the
 * optimizer reads it from the image instead of folding the marker into code.
 *
 * argv[0] rule. The launcher's own arguments are everything after the program
 * name in GetCommandLineW(). The program name is skipped the way the C runtime
 * parses it: a double quote toggles a quoted state, and the name ends at the
 * first space or tab outside quotes; the spaces and tabs after it are skipped
 * too. The tail is never re-parsed or re-quoted.
 *
 * Variants (see launcher/build.py): the console build (wmain) shares the
 * console with the child and lets Ctrl+C reach it; the GUI build (wWinMain,
 * compiled with -DPYRETORT_GUI) has no console, starts the child with
 * CREATE_NO_WINDOW and reports start-up errors in a message box.
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <string.h>
#include <wchar.h>

#define COMMAND_CAPACITY 1024
#define EXE_DIR_MARKER L"{EXE_DIR}"

__attribute__((used)) volatile wchar_t command_template[COMMAND_CAPACITY] =
    L"PYRETORT-LAUNCHER-COMMAND-PLACEHOLDER";

/* Title of the GUI error box; replaced with the launcher's file name. */
static const wchar_t *error_title = L"Launcher";

static void *allocate(size_t bytes) {
    return HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, bytes);
}

#ifndef PYRETORT_GUI
static void write_to_stderr(const wchar_t *text) {
    HANDLE handle = GetStdHandle(STD_ERROR_HANDLE);
    DWORD length = (DWORD)wcslen(text);
    DWORD mode;
    DWORD written;
    if (handle == NULL || handle == INVALID_HANDLE_VALUE) {
        return;
    }
    if (GetConsoleMode(handle, &mode)) {
        WriteConsoleW(handle, text, length, &written, NULL);
        return;
    }
    int size = WideCharToMultiByte(CP_UTF8, 0, text, (int)length, NULL, 0, NULL, NULL);
    char *utf8 = allocate((size_t)size);
    if (utf8 == NULL) {
        return;
    }
    if (WideCharToMultiByte(CP_UTF8, 0, text, (int)length, utf8, size, NULL, NULL) > 0) {
        WriteFile(handle, utf8, (DWORD)size, &written, NULL);
    }
    HeapFree(GetProcessHeap(), 0, utf8);
}
#endif

static void report(const wchar_t *message) {
#ifdef PYRETORT_GUI
    MessageBoxW(NULL, message, error_title, MB_OK | MB_ICONERROR);
#else
    write_to_stderr(message);
    write_to_stderr(L"\r\n");
#endif
}

/* Report "Cannot start <subject>: <system message>" and exit with code 1. */
static void die(const wchar_t *subject, DWORD error_code) {
    wchar_t *reason = NULL;
    FormatMessageW(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM |
                       FORMAT_MESSAGE_IGNORE_INSERTS,
                   NULL, error_code, 0, (LPWSTR)&reason, 0, NULL);
    if (reason == NULL) {
        reason = L"unknown error";
    }
    size_t reason_length = wcslen(reason);
    while (reason_length > 0 &&
           (reason[reason_length - 1] == L'\r' || reason[reason_length - 1] == L'\n')) {
        reason[--reason_length] = L'\0';
    }
    size_t size = (wcslen(subject) + reason_length + 16) * sizeof(wchar_t);
    wchar_t *message = allocate(size);
    if (message == NULL) {
        report(L"Cannot start the application: out of memory");
    } else {
        wcscpy(message, L"Cannot start ");
        wcscat(message, subject);
        wcscat(message, L": ");
        wcscat(message, reason);
        report(message);
    }
    ExitProcess(1);
}

static void *allocate_or_die(size_t bytes) {
    void *memory = allocate(bytes);
    if (memory == NULL) {
        die(L"the application", ERROR_NOT_ENOUGH_MEMORY);
    }
    return memory;
}

static wchar_t *duplicate(const wchar_t *text) {
    size_t size = (wcslen(text) + 1) * sizeof(wchar_t);
    wchar_t *copy = allocate_or_die(size);
    memcpy(copy, text, size);
    return copy;
}

/* Full path of this executable; the buffer grows until the path fits. */
static wchar_t *module_path(void) {
    DWORD size = MAX_PATH;
    for (;;) {
        wchar_t *buffer = allocate_or_die(size * sizeof(wchar_t));
        DWORD length = GetModuleFileNameW(NULL, buffer, size);
        if (length == 0) {
            die(L"the application", GetLastError());
        }
        if (length < size) {
            return buffer;
        }
        HeapFree(GetProcessHeap(), 0, buffer);
        size *= 2;
    }
}

/* The command line after the program name; see the argv[0] rule above. */
static const wchar_t *arguments_tail(const wchar_t *p) {
    BOOL quoted = FALSE;
    for (; *p; p++) {
        if (*p == L'"') {
            quoted = !quoted;
        } else if (!quoted && (*p == L' ' || *p == L'\t')) {
            break;
        }
    }
    while (*p == L' ' || *p == L'\t') {
        p++;
    }
    return p;
}

/* A copy of command with every {EXE_DIR} replaced by exe_dir. */
static wchar_t *expand_exe_dir(const wchar_t *command, const wchar_t *exe_dir) {
    const size_t marker_length = wcslen(EXE_DIR_MARKER);
    const size_t dir_length = wcslen(exe_dir);
    size_t count = 0;
    for (const wchar_t *hit = wcsstr(command, EXE_DIR_MARKER); hit != NULL;
         hit = wcsstr(hit + marker_length, EXE_DIR_MARKER)) {
        count++;
    }
    wchar_t *result =
        allocate_or_die((wcslen(command) + count * dir_length + 1) * sizeof(wchar_t));
    wchar_t *out = result;
    const wchar_t *in = command;
    for (const wchar_t *hit = wcsstr(in, EXE_DIR_MARKER); hit != NULL;
         hit = wcsstr(in, EXE_DIR_MARKER)) {
        size_t prefix_length = (size_t)(hit - in);
        memcpy(out, in, prefix_length * sizeof(wchar_t));
        out += prefix_length;
        memcpy(out, exe_dir, dir_length * sizeof(wchar_t));
        out += dir_length;
        in = hit + marker_length;
    }
    wcscpy(out, in);
    return result;
}

/* command, then a space and the tail when the launcher got arguments. */
static wchar_t *join_command_line(const wchar_t *command, const wchar_t *tail) {
    size_t size = (wcslen(command) + 1 + wcslen(tail) + 1) * sizeof(wchar_t);
    wchar_t *line = allocate_or_die(size);
    wcscpy(line, command);
    if (*tail != L'\0') {
        wcscat(line, L" ");
        wcscat(line, tail);
    }
    return line;
}

/* Pass the std handles that exist on to the child. */
static void inherit_std_handles(STARTUPINFOW *startup) {
    HANDLE handles[3] = {GetStdHandle(STD_INPUT_HANDLE), GetStdHandle(STD_OUTPUT_HANDLE),
                         GetStdHandle(STD_ERROR_HANDLE)};
    BOOL any = FALSE;
    for (int i = 0; i < 3; i++) {
        if (handles[i] != NULL && handles[i] != INVALID_HANDLE_VALUE) {
            SetHandleInformation(handles[i], HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT);
            any = TRUE;
        }
    }
    if (any) {
        startup->dwFlags |= STARTF_USESTDHANDLES;
        startup->hStdInput = handles[0];
        startup->hStdOutput = handles[1];
        startup->hStdError = handles[2];
    }
}

/* A job that kills its processes when the last handle to it closes. */
static HANDLE create_kill_on_close_job(void) {
    HANDLE job = CreateJobObjectW(NULL, NULL);
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits;
    if (job == NULL) {
        return NULL;
    }
    ZeroMemory(&limits, sizeof(limits));
    limits.BasicLimitInformation.LimitFlags =
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK;
    if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation, &limits,
                                 sizeof(limits))) {
        CloseHandle(job);
        return NULL;
    }
    return job;
}

#ifndef PYRETORT_GUI
/* Ctrl+C goes to the child, which shares the console; the launcher waits. */
static BOOL WINAPI ignore_console_signal(DWORD signal) {
    (void)signal;
    return TRUE;
}
#endif

static int run(void) {
    wchar_t command[COMMAND_CAPACITY];
    for (size_t i = 0; i < COMMAND_CAPACITY; i++) {
        command[i] = command_template[i];
    }
    command[COMMAND_CAPACITY - 1] = L'\0';

    wchar_t *exe_dir = module_path();
    wchar_t *last_backslash = wcsrchr(exe_dir, L'\\');
    if (last_backslash != NULL) {
        error_title = duplicate(last_backslash + 1);
        *last_backslash = L'\0';
    }

    wchar_t *expanded = expand_exe_dir(command, exe_dir);
    wchar_t *command_line = join_command_line(expanded, arguments_tail(GetCommandLineW()));
    /* CreateProcessW may edit its command line buffer; keep a copy to report. */
    wchar_t *reported_command_line = duplicate(command_line);

    STARTUPINFOW startup;
    PROCESS_INFORMATION process;
    ZeroMemory(&startup, sizeof(startup));
    startup.cb = sizeof(startup);
    inherit_std_handles(&startup);
    DWORD flags = CREATE_SUSPENDED;
#ifdef PYRETORT_GUI
    flags |= CREATE_NO_WINDOW;
#endif
    if (!CreateProcessW(NULL, command_line, NULL, NULL, TRUE, flags, NULL, NULL, &startup,
                        &process)) {
        die(reported_command_line, GetLastError());
    }

    HANDLE job = create_kill_on_close_job();
    if (job != NULL) {
        AssignProcessToJobObject(job, process.hProcess);
    }
#ifndef PYRETORT_GUI
    SetConsoleCtrlHandler(ignore_console_signal, TRUE);
#endif
    if (ResumeThread(process.hThread) == (DWORD)-1) {
        DWORD error_code = GetLastError();
        TerminateProcess(process.hProcess, 1);
        die(reported_command_line, error_code);
    }
    CloseHandle(process.hThread);

    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD exit_code = 1;
    if (!GetExitCodeProcess(process.hProcess, &exit_code)) {
        exit_code = 1;
    }
    CloseHandle(process.hProcess);
    if (job != NULL) {
        CloseHandle(job);
    }
    return (int)exit_code;
}

#ifdef PYRETORT_GUI
int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR command_line, int show) {
    (void)instance;
    (void)previous;
    (void)command_line;
    (void)show;
    return run();
}
#else
int wmain(int argc, wchar_t **argv) {
    (void)argc;
    (void)argv;
    return run();
}
#endif
