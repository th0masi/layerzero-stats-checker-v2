import {reactive, html, watch} from 'https://cdn.skypack.dev/@arrow-js/core'

document.addEventListener("DOMContentLoaded", () => {
  const addressList = document.getElementById("addressList")
  const addIdSwitch = document.getElementById("addIdSwitch")
  const proxyList = document.getElementById("proxyList")
  const submitButton = document.getElementById("submitButton")
  const addressIdFormItem = document.getElementById("addressIdFormItem")
  const formState = reactive({
    addId: addIdSwitch.checked,
    formSending: false,
    addressListValue: addressList.value,
  })
  addIdSwitch.onchange = (e) => {
    formState.addId = e.target.checked;
  }
  watch(() => {
    const val = formState.addId;

    if (!val) {
      const addressFormItem = document.getElementById("addressFormItem")
      addressFormItem.className = "item item--wide"
      addressIdFormItem.className = "item item--hide"
    } else {
      const addressFormItem = document.getElementById("addressFormItem")
      addressFormItem.className = "item"
      const addressIdFormItem = document.getElementById("addressIdFormItem")
      addressIdFormItem.className = "item"
    }
  })
  addressList.oninput = (e) => {
    formState.addressListValue = !!e.target.value
  }
  watch(()=>{
      submitButton.toggleAttribute("disabled", !formState.addressListValue);
  })

  submitButton.onclick = (e) => {
    setTimeout(()=>{formState.formSending = true;}, 10)
  }
  watch(() => {
    if (!formState.formSending) return;
    submitButton.toggleAttribute("disabled", true)
    addressList.toggleAttribute("disabled", true)
    proxyList.toggleAttribute("disabled", true)
  })

});
