from jinja2 import Environment, FileSystemLoader

templateLoader = FileSystemLoader(searchpath="app/templates/system_templates")
templateEnv = Environment(loader=templateLoader)


class MessageTemplateActions:

    @staticmethod
    async def create_auth_email(auth_url):
        return templateEnv.get_template("auth.html").render(
            AUTH_URL=auth_url
        )

    @staticmethod
    async def create_auth_code_add_service_email(auth_code):
        return templateEnv.get_template("add_service_code.html").render(
            AUTH_CODE=auth_code
        )

    @staticmethod
    async def get_recipient_first_name(recipient):
        return recipient["user"].first_name

    @staticmethod
    async def get_recipient_last_name(recipient):
        return recipient["user"].last_name
