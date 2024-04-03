import {reactive, html, watch} from 'https://cdn.skypack.dev/@arrow-js/core'

document.addEventListener("DOMContentLoaded", () => {
  const url = new URL(window.location);

  document.querySelectorAll(".js-toggle").forEach((toggle) => {
    toggle.onclick = (e) => {
      toggle.classList.toggle("open");
    };
  });

  const state = reactive({
    showAddresses: true,
  })

  document.querySelectorAll(".header__button").forEach((button) => {
    let isActive = button.href ? ((new URL(button.href)).pathname === url.pathname) : false;
    if (isActive) {
      button.className = "header__button header__button--active";
      button.onclick = (e) => {
        e.preventDefault();
      }
    }
  });

  function showAddressesFunc() {
    if (state.showAddresses) {
      const button = document.getElementById("showAddressesToggle");
      button.className = 'header__button header__button--eye'
    } else {
      const button = document.getElementById("showAddressesToggle");
      button.className = 'header__button header__button--active header__button header__button--eye-closed'
    }
    document.body.setAttribute('data-hidden', state.showAddresses ? "0" : "1")
  }
  watch(showAddressesFunc)
  document.getElementById("showAddressesToggle").onclick = () => {
    state.showAddresses = !state.showAddresses;
  }

  // Wallet page
  const srcNetworksSwitch = document.getElementById("srcNetworksSwitch")
  if (srcNetworksSwitch) {
    srcNetworksSwitch.checked = false;
    srcNetworksSwitch.onchange = (e) => {
      const val = e.target.checked;
      document.getElementById("srcNetworksContainer").setAttribute("data-enabled", val ? "0" : "1");
    }
  }
  const destNetworksSwitch = document.getElementById("destNetworksSwitch")
  if (destNetworksSwitch) {
    destNetworksSwitch.checked = false;
    destNetworksSwitch.onchange = (e) => {
      const val = e.target.checked;
      document.getElementById("destNetworksContainer").setAttribute("data-enabled", val ? "0" : "1");
    }}
  const protocolSwitch = document.getElementById("protocolSwitch")
  if (protocolSwitch) {
    protocolSwitch.checked = false;
    protocolSwitch.onchange = (e) => {
      const val = e.target.checked;
      document.getElementById("protocolContainer").setAttribute("data-enabled", val ? "0" : "1");
    }
  }

  // Stats page
  const srcNetworksStatsSwitch = document.getElementById("srcNetworksStatsSwitch")
  const destNetworksStatsSwitch = document.getElementById("destNetworksStatsSwitch")
  const protocolStatsSwitch = document.getElementById("protocolStatsSwitch")
  if (srcNetworksStatsSwitch) {
    srcNetworksStatsSwitch.onchange = (e) => {
      const val = e.target.checked;
      document.getElementById("srcNetworksStatsContainer").setAttribute("data-enabled", val ? "0" : "1")
    }
  }
  if (destNetworksStatsSwitch) {
    destNetworksStatsSwitch.onchange = (e) => {
      const val = e.target.checked;
      document.getElementById("destNetworksStatsContainer").setAttribute("data-enabled", val ? "0" : "1")
    }
  }
  if (protocolStatsSwitch) {
    protocolStatsSwitch.onchange = (e) => {
      const val = e.target.checked;
      document.getElementById("protocolStatsContainer").setAttribute("data-enabled", val ? "0" : "1")
    }
  }
});
