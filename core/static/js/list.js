import {reactive, html, watch} from 'https://cdn.skypack.dev/@arrow-js/core'


function formatNumber(value) {
    if (!value) {
        return value;
    }
    if (typeof value === "number" && isFinite(value)) {
        return value.toLocaleString("en-US").replace(/\,/g, " ");
    } else {
        return parseFloat(value).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    }
}


document.addEventListener("DOMContentLoaded", () => {
    const state = reactive({
        showId: false,
        showLogs: false,
        walletList: [],
        walletListLoading: true,
        searchValue: "",
        isUpdaterStarted: initialFlaskState.isUpdaterStarted,
        sortBy: "",
        sortOrder: "",
    })

    const searchInput = document.getElementById('searchInput')
    searchInput.oninput = e => {
        state.searchValue = e.target.value
    }

    const walletList = document.getElementById('walletList')
    const walletListHeader = document.getElementById('walletListHeader')
    const walletListShowIdSwitch = document.getElementById("walletListShowIdSwitch")
    const refreshHeaderButton = document.getElementById('refreshHeaderButton')
    const formHeaderButton = document.getElementById('formHeaderButton')
    const downloadHeaderButton = document.getElementById('downloadHeaderButton')
    const columnsElements = [
        document.getElementById("columnBalanceHeader"),
        document.getElementById("columnRankHeader"),
        document.getElementById("columnVolumeHeader"),
        document.getElementById("columnTransHeader"),
        document.getElementById("columnSourceHeader"),
        document.getElementById("columnProtocolHeader"),
        document.getElementById("columnActivityHeader"),
        document.getElementById("columnDownloadedHeader"),
        document.getElementById("columnUpdatedHeader")
    ]
    columnsElements.forEach((headerElem) => {
        headerElem.onclick = () => {
            if (state.sortBy && state.sortBy === headerElem.getAttribute("data-column")) {
                state.sortOrder = state.sortOrder === 'asc' ? "desc" : "asc";
            } else {
                state.sortBy = headerElem.getAttribute("data-column")
                state.sortOrder = "desc";
            }
        }
    })
    watch(() => !!state.sortBy && columnsElements.forEach((headerElem) => {
        if (state.sortBy !== headerElem.getAttribute("data-column")) return headerElem.toggleAttribute("data-sort", false);
        headerElem.setAttribute("data-sort", state.sortOrder);
    }))


    // ID Toggle
    walletListShowIdSwitch.checked = false;
    walletListShowIdSwitch.onchange = (e) => {
        state.showId = e.target.checked;
    }

    watch(() => walletList.setAttribute('data-show-id', state.showId ? "1" : "0"))

    function updateWalletList() {
        // Reloader
        state.walletListLoading = true;
        return fetch('getWalletList').then(r => r.json()).then(r => {
            state.walletList = r.results
            state.walletListLoading = false;
            state.isUpdaterStarted = r.isUpdaterStarted;
            return r
        })
    }
    const UPDATE_INTERVAL = 2500;

    updateWalletList().then(()=>{
        let updateIntervalId = null;
        watch(() => {
            if (state.isUpdaterStarted) {
                if (updateIntervalId != null) {
                    clearTimeout(updateIntervalId)
                    updateIntervalId = null
                }
                const setUpdateIntervalId = () => {
                    updateIntervalId = setTimeout(() => {
                        if (state.isUpdaterStarted) updateWalletList().then(() => {
                            if (state.isUpdaterStarted) setUpdateIntervalId();
                        });
                    }, UPDATE_INTERVAL)
                }
                setUpdateIntervalId();
            } else {
                clearTimeout(updateIntervalId)
                updateIntervalId = null
            }
        })
    });

    // refreshHeaderButton.onclick = (e) => {updateWalletList()}
    watch(()=>{
        refreshHeaderButton.toggleAttribute("aria-disabled", state.isUpdaterStarted)
        formHeaderButton.toggleAttribute("aria-disabled", state.isUpdaterStarted)
        downloadHeaderButton.toggleAttribute("aria-disabled", state.isUpdaterStarted)
    })

    html`
        ${
            () => (state.walletListLoading || state.isUpdaterStarted)
                ?
                html`
                    <div class="update"></div>
                    <div>
                        Обновление
                    </div>
                `
                : 
                html`
                    <div>
                        Результаты
                        ${() => state.walletList.filter(w => w.address.includes(state.searchValue)).length}
                        адресов
                    </div>
                `
        }
    `(walletListHeader);
    html`${() => state.walletList.filter(w => w.address.includes(state.searchValue)).toSorted((_a, _b) => {
        let a = state.sortOrder === "asc" ? _b : _a
        let b = state.sortOrder === "asc" ? _a : _b

        if (state.sortBy === 'trans') return a.count_txn - b.count_txn;
        if (state.sortBy === 'balance') return a.balance_usd - b.balance_usd;
        if (state.sortBy === 'rank') return a.current_rank - b.current_rank;
        if (state.sortBy === 'volume') return a.volume - b.volume;
        if (state.sortBy === 'source') return a.src_chains_count - b.src_chains_count;
        if (state.sortBy === 'protocol') return a.protocol_count - b.protocol_count;
        if (state.sortBy === 'activity') return a.months - b.months;
        if (state.sortBy === 'downloaded') return a.last_activity - b.last_activity;
        if (state.sortBy === 'updated') return a.last_update - b.last_update;
        
        return 0;
    }).map(wallet => html`
        <a href="/wallet/${wallet.address}" class="table-item">
            <div class="cell cell-lg">
                <div>
                    <span data-hide="1">${wallet.address}</span><span
                        data-hide="0">${wallet.address.replaceAll(/[a-zA-Z]/gi, "x")}</span>
                </div>
                ${() => wallet.wname ? html`
                    <div data-show-id>
                        ${wallet.wname}
                    </div>
                ` : null}
            </div>
            <div class="cell">
                <div>${formatNumber(wallet.current_rank)}</div>
                ${wallet.prev_rank ? html`
                    <div>
                        ${(wallet.prev_rank - wallet.current_rank) > 0
                                ?
                                html`<span class="positive">+${wallet.prev_rank - wallet.current_rank}</span>`
                                : (wallet.prev_rank - wallet.current_rank) < 0
                                        ?
                                        html`<span class="negative">-${wallet.prev_rank - wallet.current_rank}</span>`
                                        :
                                        ""}
                    </div>
                ` : ""}
            </div>
            <div class="cell">${formatNumber(wallet.volume)} $</div>
            <div class="cell">${wallet.count_txn}</div>
            <div class="cell">${wallet.src_chains_count} / ${wallet.dst_chains_count}</div>
            <div class="cell">${wallet.protocol_count}</div>
            <div class="cell">${wallet.months} мес.</div>
            <div class="cell">${formatNumber(wallet.balance_usd)} $</div>
            <div class="cell">${wallet.last_activity}</div>
            <div class="cell">${wallet.last_update}</div>
        </a>
    `)}`(walletList);
});
