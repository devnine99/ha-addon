import paho.mqtt.client as mqtt

if __name__ == "__main__":
    mqtt_client = mqtt.Client("ezvill-test", userdata={})
    mqtt_client.username_pw_set("mqtt-user", "55ba1f50-24cd-427d-9cb0-439e7061eb04")
    mqtt_client.connect("192.168.45.14", 1883, 60)

    def on_connect(client, userdata, flags, rc):
        print(rc)
        client.subscribe([("ew11/state", 0)])

    data = {}

    def on_message(client, userdata, message):
        if message.topic == "ew11/state":
            payload = message.payload.hex()
            if "f70e1141030121008a06" in payload:
                print(payload)
            # for state in payload.replace("f7", "/f7").split("/"):
            #     print(state)
            # if state.startswith("f732"):
            #     print(state)
            # data[state] = data.get(state, 0) + 1
            # if data[state] == 5:
            #     print(state)
            return

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    # mqtt_client.loop_forever()
    mqtt_client.publish("ew11/set", bytes.fromhex("f70e1141030121008a06"))
