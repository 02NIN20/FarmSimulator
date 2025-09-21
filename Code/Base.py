from pyray import *
from raylib import *

windowXvalue = 1280
windowYvalue = 720

windowXtext = int(windowXvalue*0.1) 
windowYtext = int(windowYvalue*0.1) 

rectX = int(windowXvalue*0.1)
rectY = int(windowYvalue*0.2)
rectW = int(windowXvalue*0.8)
rectH = int(windowYvalue*0.6)

rect = [rectX,rectY,rectW,rectH]
#rectRound = ()

init_window(windowXvalue,windowYvalue, 'Base')

while not window_should_close():
    begin_drawing()
    clear_background(BROWN)
    draw_text('Hello, World!', windowXtext, windowYtext, 20, WHITE)
    draw_rectangle_rounded(rect, 0.2, 10, RED)
    end_drawing()

close_window()