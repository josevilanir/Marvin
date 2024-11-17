import webbrowser


def abrir_navegador_com_pesquisa(pesquisa):
    url = f"https://www.google.com/search?q={pesquisa}"
    webbrowser.open(url)
