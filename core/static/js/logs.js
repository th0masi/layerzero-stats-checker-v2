import {reactive, html, watch} from 'https://cdn.skypack.dev/@arrow-js/core'

document.addEventListener("DOMContentLoaded", () => {
    const state = reactive({
        loglines: [],
    });
    const logContainer = document.getElementById("logContainer");
    fetch("/getLogs").then(r => r.json()).then(r => {
        state.loglines = r;
        setInterval(() => {
            fetch("/getLogs").then(r => r.json()).then(r => {
                state.loglines = r;
            })
        }, 4000);
    })
    html`${() => state.loglines.map(line => html`<div class="wallet-list-page-logs__logline">${ line }</div>`)}`(logContainer);
});
