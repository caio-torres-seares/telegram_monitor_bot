class Pessoa:
    def __init__(self, nome, phone_number=None, whatsapp_number=None, whatsapp_api=None, keywords=None):
        self.nome = nome
        self.phone_number = phone_number
        self.whatsapp_api = whatsapp_api
        self.keywords = keywords or []
