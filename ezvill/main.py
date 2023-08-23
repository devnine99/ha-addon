import json
import random
import time
from datetime import datetime

import paho.mqtt.client as mqtt

APP = "ezvill"
COMMAND_TOPIC = f"{APP}/set"
STATE_TOPIC = f"{APP}/state"

RC_STATE = {
    0: "Connection successful",
    1: "Connection refused - incorrect protocol version",
    2: "Connection refused - invalid client identifier",
    3: "Connection refused - server unavailable",
    4: "Connection refused - bad username or password",
    5: "Connection refused - not authorised",
}


def log(message):
    print(f"[{datetime.now().isoformat()}] {message}")


class HA:
    def __init__(self, client, device_set):
        self.client = client
        self.device_set = device_set

    def discovery(self):
        for device in self.device_set:
            kind = device.pop("kind")
            room_name = device.pop("room_name")
            device_name = device.pop("device_name")
            unique_id = device.pop("unique_id")
            on = device.pop("on")
            off = device.pop("off")
            self.client.publish(
                f"homeassistant/{kind}/{unique_id}/config",
                json.dumps(
                    {
                        "name": device_name,
                        "unique_id": unique_id,
                        "command_topic": f"{APP}/set",
                        "state_topic": f"{APP}/state",
                        "payload_on": f"{unique_id}/on/{on}/0",
                        "payload_off": f"{unique_id}/off/{off}/0",
                        "device": {
                            "name": room_name,
                            "identifiers": room_name,
                            "manufacturer": APP,
                            "model": "wallpad",
                            "suggested_area": room_name,
                        },
                    }
                ),
            )


def run_forever(options):
    device_set = options["device_set"]
    unique_device_set = {device["unique_id"]: device for device in device_set}
    device_state_set = {
        *{d for data in device_set for d in data["state_on"]},
        *{d for data in device_set for d in data["state_off"]},
    }
    mqtt_client = mqtt.Client(APP, userdata={})
    mqtt_client.username_pw_set(options["mqtt_id"], options["mqtt_pw"])
    mqtt_client.connect(options["mqtt_ip"], options["mqtt_port"], 60)
    ha = HA(mqtt_client, device_set)
    ha.discovery()

    def on_connect(client, userdata, flags, rc):
        log(RC_STATE[rc])
        if rc == 0:
            client.subscribe([(options["ew11_pub_topic"], 0), (COMMAND_TOPIC, 0)])
        else:
            log("MQTT 연결에 실패했습니다.")
            raise Exception("MQTT 연결에 실패했습니다.")

    def on_message(client, userdata, message):
        if message.topic == options["ew11_pub_topic"]:
            payload = message.payload.hex()
            for state in payload.replace("f7", "/f7").split("/"):
                if state in device_state_set:
                    userdata[state] = time.time()
                    client.user_data_set(userdata)
            return

        if message.topic == COMMAND_TOPIC:
            userdata = userdata
            payload = message.payload.decode()
            unique_id, onoff, command, retry = payload.split("/")
            retry = int(retry)
            max_on = max([userdata.get(s, 0) for s in unique_device_set[unique_id][f"state_{onoff}"]])
            max_off = max(
                [userdata.get(s, 0) for s in unique_device_set[unique_id][f"state_{'off' if onoff == 'on' else 'on'}"]]
            )
            if unique_id != "elevator" and max_on > max_off:
                client.publish(STATE_TOPIC, "/".join([unique_id, onoff, command, str(0)]))
                return
            if unique_id == "elevator" and max_on > time.time() - 5:
                client.publish(STATE_TOPIC, "/".join([unique_id, "off", "f7330181030024006335", str(0)]))
                return
            if int(retry) >= 100:
                return
            client.publish(options["ew11_sub_topic"], bytes.fromhex(command))
            time.sleep(0.2 * random.random())
            client.publish(message.topic, "/".join([unique_id, onoff, command, str(int(retry) + 1)]))
            return

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.loop_start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    log("ezvill addon 시작.")
    with open("/data/options.json") as json_file:
        OPTIONS = json.load(json_file)
    run_forever(OPTIONS)
