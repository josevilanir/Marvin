from pynput import mouse


def on_click(x, y, button, pressed ):
    
    if not pressed and button == mouse.Button.middle:

        print(x, y)


with mouse.Listener(on_click=on_click) as coordenadas:
    
    coordenadas.join()

on_click()