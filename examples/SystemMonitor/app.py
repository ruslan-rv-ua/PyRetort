import asyncio
import threading
import time

import htpy as h
import psutil
import uvicorn
import webview
from datastar_py.fastapi import DatastarResponse, ReadSignals, ServerSentEventGenerator
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


def create_metric_card(title_text: str, data_key: str):
    """Create a metric card with title, and data binding."""
    return h.div(".col-md-6")[
        h.div(".card.bg-dark.p-4")[
            h.div(".card-body")[
                h.div[h.h2(".h5.text-white")[title_text],],
                h.div[h.span(".h4", data_text=f"${data_key}")],
            ]
        ]
    ]


def render_page():
    """Render the system monitor page using htpy."""
    return str(
        h.html(lang="en", data_bs_theme="dark")[
            h.head[
                h.title["System Monitor"],
                h.meta(charset="utf-8"),
                h.meta(
                    name="viewport", content="width=device-width, initial-scale=1.0"
                ),
                h.link(
                    rel="stylesheet",
                    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
                ),
                h.script(
                    type="module",
                    src="https://cdn.jsdelivr.net/gh/starfederation/datastar@main/bundles/datastar.js",
                ),
            ],
            h.body(
                ".min-vh-100.bg-dark.text-white.d-flex.flex-column.align-items-center.justify-content-center.p-4",
                data_signals='{"cpuUsage": "0.0%", "memoryUsage": "0.0%"}',
            )[
                h.header(".mb-5.text-center")[h.h1(".display-4")["Real-time monitor"]],
                h.div(
                    ".row.w-100.justify-content-center",
                    data_on_load="@get('/updates')",
                )[
                    create_metric_card("CPU Usage", "cpuUsage"),
                    create_metric_card("Memory Usage", "memoryUsage"),
                ],
            ],
        ]
    )


@app.get("/")
async def read_root():
    return HTMLResponse(render_page())


async def system_updates():
    """Generate real-time system metrics updates."""
    while True:
        yield ServerSentEventGenerator.patch_signals(
            {
                "cpuUsage": f"{psutil.cpu_percent(interval=1)}%",
                "memoryUsage": f"{psutil.virtual_memory().percent}%",
            }
        )
        await asyncio.sleep(3)


@app.get("/updates")
async def updates(signals: ReadSignals):
    return DatastarResponse(system_updates())


def start_server():
    uvicorn.run(app, host="127.0.0.1", port=9999)


if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    time.sleep(1.5)
    webview.create_window("System Monitor", "http://127.0.0.1:9999", fullscreen=True)
    webview.start()
