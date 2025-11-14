import requests
import json

class UUIDHandler:
    def __init__(self):
        self.agent_uuid_request = None

    def agent_uuid_function(self):
        try:
            with open("agent_uuids.json") as a:
                self.agent_uuids = json.load(a)
        except FileNotFoundError:
            self.agent_uuid_request = requests.get("https://valorant-api.com/v1/agents").json()
            print("requested agent uuid information from valorant-api.com")

            with open("agent_uuids.json", "w", encoding="utf-8") as f:
                json.dump(self.agent_uuid_request, f, indent=2)

            with open("agent_uuids.json") as a:
                self.agent_uuids = json.load(a)

    def agent_converter(self, uuid):
        result = []
        for agent in self.agent_uuids["data"]:
            if agent["uuid"] == uuid.lower():
                result = agent["displayName"]
        return result

    def agent_converter_reversed(self, agent_name):
        result = []
        for agent in self.agent_uuids["data"]:
            if agent["displayName"].lower() == agent_name.lower():
                result = agent["uuid"]
        return result

    def skin_uuid_function(self):
        try:
            with open("skin_uuids.json") as a:
                self.skin_uuids = json.load(a)
        except FileNotFoundError:
            self.skin_uuid_request = requests.get("https://valorant-api.com/v1/weapons/skins").json()
            print("requested skin uuid information from valorant-api.com")

            with open("skin_uuids.json", "w", encoding="utf-8") as f:
                json.dump(self.skin_uuid_request, f, indent=2)

            with open("agent_uuids.json") as a:
                self.skin_uuids = json.load(a)

    def skin_converter(self, skin_uuid):
        result = []
        for skin in self.skin_uuids["data"]:
            if skin["uuid"] == skin_uuid:
                result = skin["displayName"]
            for chroma in skin["chromas"]:
                if chroma["uuid"] == skin_uuid:
                    result = chroma["displayName"]
        print(result)
        return result





