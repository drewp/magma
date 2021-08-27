const setLivingTo = (level) => {
    for (let s of [
      "/rdf_to_mqtt/output?s=:livingLampShelf&p=:brightness",
      "/rdf_to_mqtt/output?s=:livingLampMantleEntry&p=:brightness",
      "/rdf_to_mqtt/output?s=:livingLampMantleChair&p=:brightness",
      "/rdf_to_mqtt/output?s=:livingLampToyShelf&p=:brightness",
      "/rdf_to_mqtt/output?s=:livingLampPiano&p=:brightness",
      "/pi/living/output?s=http%3A%2F%2Fprojects.bigasterisk.com%2Froom%2FlivingRoomLamp3&p=http%3A%2F%2Fprojects.bigasterisk.com%2Froom%2Fbrightness",
    ]) {
      setTimeout(() => {
        fetch(s, { method: "PUT", body: level });
      }, Math.random() * 1200);
    }
  };

  const setKitchenTo = (level) => {
    for (let s of ["/rdf_to_mqtt/output?s=:kitchenLight&p=:brightness", "/rdf_to_mqtt/output?s=:kitchenCounterLight&p=:brightness"]) {
      const scale = s.indexOf("Counter") != -1 ? 0.5 : 1.0;
      fetch(s, { method: "PUT", body: level * scale });
    }
  };

  document.querySelector("#livingLampsOn").addEventListener("click", () => {
    setLivingTo("1.0");
  });

  document.querySelector("#livingLampsOff").addEventListener("click", () => {
    setLivingTo("0.0");
  });
  document.querySelector("#kitchenLampsOn").addEventListener("click", () => {
    setKitchenTo("1.0");
  });

  document.querySelector("#kitchenLampsOff").addEventListener("click", () => {
    setKitchenTo("0.0");
  });

  document.querySelector("#frontDoorUnlock").addEventListener("click", () => {
    fetch("/frontDoorLock/output", {
      headers: {
        "content-type": "text/n3",
      },
      body:
        "<http://projects.bigasterisk.com/room/frontDoorLock> <http://projects.bigasterisk.com/room/state> <http://projects.bigasterisk.com/room/unlocked> .",
      method: "POST",
      mode: "cors",
      credentials: "include",
    });
  });

  Array.from(document.querySelectorAll("button.to_mqtt")).forEach((el) => {
    el.addEventListener("click", (ev) => {
      fetch(el.dataset.post, {
        method: "PUT",
        body: el.dataset.body,
      });
    });
  });

fetch("https://bigasterisk.com/prometheus/api/v1/query?query=air", {
  "mode": "cors",
  "credentials": "include"
}).then((resp) => {
  return resp.json();
}).then((doc) => {
  const el = document.querySelector('#sensors');
  doc.data.result.forEach((row) => {
    const rowEl = document.createElement('div');
    const href = `/prometheus/graph?g0.expr=air%7Btype%3D%22${row.metric.type}%22%7D&g0.tab=0&g0.range_input=2h`
    rowEl.innerHTML = `<a href="${href}">${row.metric.loc} ${row.metric.type} = ${row.value[1]}</a>`;
    el.appendChild(rowEl);
  })
});