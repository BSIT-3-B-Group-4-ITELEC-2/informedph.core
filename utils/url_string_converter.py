from pydantic import HttpUrl, TypeAdapter


def url_string_converter(url):
    url_adapter = TypeAdapter(HttpUrl)

    converted_url_string = url_adapter.validate_python(url)

    return converted_url_string
