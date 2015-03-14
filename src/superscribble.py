# Copyright (c) 2009 Nokia Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modified by Jose Sousa
#
# Renamed to Super Scribble
# v0.4


import appuifw
import e32
import os
import time
import operator
from graphics import *
from key_codes import *


class PaintApp():
    BG_COLOR = (255,255,255) # white
    BORDER_COLOR = (0,0,0) # black
    BRUSH_COLOR = (0,0,0) # black
    MODE_ACTIVE = (255,0,0) # Red
    MODE_SAMPLE = (255,255,0)
    AREA_INACTIVE = (192,192,192)
    MAX_WIDTH = 32
    MAX_MIX   = 150
    IMAGE_SIZE = (720,1280)
    IMAGE_POS = (0,0)
    IMAGE_ZOOM = 100
    
    def __init__(self):
        # main app setup
        appuifw.app.exit_key_handler = self.quit
        appuifw.app.directional_pad = False
        # app variables
        self.drive = unicode(os.getcwd()[0])
        # app flags
        self.running = True
        self.saving_file = False
        self.orientation_changed = False
        self.bind_palette = True
        self.about_active = False
        self.is_about_active = False
        # erase tool variables
        self.erase_mode = 0
        # mix tool variables
        self.mix_mode = 0
        self.mix_counter = 1
        self.mix_dist = 10
        self.mix_init = (0,0,0)
        # opacity tool variables
        self.opacity_value = 255
        self.opacity_active = False
        # move tool variables
        self.move_active = False
        # brush defaults init
        self.new_color = (0,0,0)
        self.BRUSH_COLOR = (0,0,0)
        self.brush_history = [(0,0,0),(255,0,0),(255,255,0),(0,255,0),(0,255,255),(0,0,255),(255,0,255),(128,128,128),(64,64,64)]
        self.pen_width = 4
        # GUI variables
        self.slider_prev_x = 0
        self.slider_prev_y = 0
        self.slider_id = -1
        # screen and canvas vars init
        self.x_max = 0
        self.y_max = 0
        self.canvas = appuifw.Canvas(event_callback=self.event_callback,
                                     redraw_callback=self.redraw_callback)
        if self.canvas.size[0] > self.canvas.size[1]:
            self.orientation = 'landscape'
        else:
            self.orientation = 'portrait'
        self.old_body = appuifw.app.body
        appuifw.app.body = self.canvas
        appuifw.app.screen = 'full'
        appuifw.app.focus = self.focus_monitor
        self.canvas.clear()
        self.draw = self.canvas
        self.draw_img = Image.new((self.IMAGE_SIZE[0], self.IMAGE_SIZE[1]))
        self.draw_area = (0,0,self.canvas.size[0],self.canvas.size[1])
        # opacity 8bit mask and buffer
        self.mask = Image.new((self.canvas.size[0], self.canvas.size[1]), 'L')
        self.draw_buf = Image.new((self.canvas.size[0], self.canvas.size[1]))
        self.mask.clear(0)
        # buttons creation
        self.draw_buttons()
        self.bind_buttons()

    def define_draw_area(self):
        if self.orientation == 'portrait':
            self.draw_area = (0,0,self.draw.size[0],self.draw.size[1]*3/4)
        else:
            self.draw_area = (0,0,self.draw.size[0]*3/4,self.draw.size[1])

    def redraw_image(self):
        self.define_draw_area()
        self.draw.rectangle((self.draw_area[0], min(self.draw_area[3], (self.IMAGE_SIZE[1]-self.IMAGE_POS[1])*self.IMAGE_ZOOM/100),
                             self.draw_area[2], self.draw_area[3]), fill=self.AREA_INACTIVE)
        self.draw.rectangle((min(self.draw_area[2], (self.IMAGE_SIZE[0]-self.IMAGE_POS[0])*self.IMAGE_ZOOM/100), self.draw_area[1],
                            self.draw_area[2], self.draw_area[3]), fill=self.AREA_INACTIVE)
        source_rect = (self.IMAGE_POS,
                      (min(self.IMAGE_POS[0]+(self.draw_area[2]-self.draw_area[0])*100/self.IMAGE_ZOOM,self.IMAGE_SIZE[0]),
                      min(self.IMAGE_POS[1]+(self.draw_area[3]-self.draw_area[1])*100/self.IMAGE_ZOOM,self.IMAGE_SIZE[1]) ) )
        target_rect = ((self.draw_area[0],self.draw_area[1]),
                       (min(self.draw_area[2], (self.IMAGE_SIZE[0]-self.IMAGE_POS[0])*self.IMAGE_ZOOM/100),
                       min(self.draw_area[3], (self.IMAGE_SIZE[1]-self.IMAGE_POS[1])*self.IMAGE_ZOOM/100) ) )
        if self.IMAGE_ZOOM == 100:
            self.draw.blit(self.draw_img, source=source_rect, target=target_rect, scale=0)
        else:
            self.draw.blit(self.draw_img, source=source_rect, target=target_rect, scale=1)

    def draw_buttons(self):
        self.x_max = self.canvas.size[0]
        self.y_max = self.canvas.size[1]
        self.pointer_advance = min(self.x_max, self.y_max) / 4
        self.toolbar_size = max(self.x_max, self.y_max) / 4
        if self.orientation == 'landscape':
            box_width = self.pointer_advance - 10
            self.menu_bar_size = self.toolbar_size / 2
            self.color_palette = self.toolbar_size - self.menu_bar_size
            draw_position = self.x_max - self.menu_bar_size
            y_displacement = (self.menu_bar_size / 2) + 10
            self.options_button = ((draw_position, 0),
                                   (self.x_max, self.pointer_advance))
            self.mix_button = ((draw_position, self.pointer_advance),
                                 (self.x_max, 2 * self.pointer_advance))
            self.eraser = ((draw_position, 2 * self.pointer_advance),
                           (self.x_max, 3 * self.pointer_advance))
            self.move_button = ((draw_position, 3 * self.pointer_advance),
                                (self.x_max, 4 * self.pointer_advance))
            self.draw.rectangle((self.x_max - self.toolbar_size, 0, self.x_max, self.y_max),
                                fill=self.BG_COLOR)
            self.draw.rectangle((self.x_max - self.toolbar_size, 0,
                                 self.x_max - self.menu_bar_size, self.y_max),
                                outline=self.BORDER_COLOR, width=5)
        else:
            box_width = self.pointer_advance
            self.menu_bar_size = self.toolbar_size / 4
            self.color_palette = self.toolbar_size - self.menu_bar_size
            draw_position = self.y_max - self.menu_bar_size
            y_displacement = (self.menu_bar_size / 2) + 5
            self.options_button = ((0, draw_position),
                                   (self.pointer_advance, self.y_max))
            self.mix_button = ((self.pointer_advance, draw_position),
                                 (2 * self.pointer_advance, self.y_max))
            self.eraser = ((self.pointer_advance * 2, draw_position),
                           (self.pointer_advance * 3, self.y_max))
            self.move_button = ((self.pointer_advance * 3, draw_position),
                                (self.pointer_advance * 4, self.y_max))
            self.draw.rectangle((0, self.y_max - self.toolbar_size, self.x_max, self.y_max),
                                fill=self.BG_COLOR)
            self.draw.rectangle((0, self.y_max - self.toolbar_size,
                                 self.x_max, self.y_max - self.menu_bar_size),
                                outline=self.BORDER_COLOR, width=5)
        # Draw the buttons at the bottom and the respective text at an offset
        # specified by x_displacement and y_displacement
        buttons = [self.options_button, self.mix_button, self.eraser,
                   self.move_button]
        options = [u'Options', u'Mix', u'Erase', u'Move']
        for button, text in zip(buttons, options):
            if self.erase_mode == 1 and text == u'Erase':
                self.draw.rectangle(self.eraser, fill=self.MODE_ACTIVE,
                                outline=self.BORDER_COLOR, width=5)
            if self.erase_mode == 2 and text == u'Erase':
                self.draw.rectangle(self.eraser, fill=self.MODE_SAMPLE,
                                outline=self.BORDER_COLOR, width=5)
                text = u'Picker'
            elif self.mix_mode == 1 and text == u'Mix':
                self.draw.rectangle(self.mix_button, fill=self.MODE_ACTIVE,
                                outline=self.BORDER_COLOR, width=5)
            elif self.mix_mode == 2 and text == u'Mix':
                self.draw.rectangle(self.mix_button, fill=self.MODE_SAMPLE,
                                outline=self.BORDER_COLOR, width=5)
                text = u'Smudge'
            elif self.move_active and text == u'Move':
                self.draw.rectangle(self.move_button, fill=self.MODE_SAMPLE,
                                outline=self.BORDER_COLOR, width=5)
            else:
                self.draw.rectangle(button, outline=self.BORDER_COLOR, width=5)
            text_dimensions = self.draw.measure_text(text)
            x_displacement = (box_width - text_dimensions[0][2]) / 2
            self.draw.text((button[0][0] + x_displacement,
                            button[0][1] + y_displacement), text,
                            font=u'Sans MT TC Big5HK_S60C',
                            fill=self.BORDER_COLOR)
        self.draw_palette()

    def bind_buttons(self):
        self.canvas.bind(EButton1Down, self.mix_callback, self.mix_button)
        self.canvas.bind(EButton1Down, self.options_callback, self.options_button)
        self.canvas.bind(EButton1Down, self.move_image, self.move_button)
        self.canvas.bind(EButton1Down, self.eraser_callback, self.eraser)

    def clear_button_bindings(self):
        self.canvas.bind(EButton1Down, None, self.mix_button)
        self.canvas.bind(EButton1Down, None, self.options_button)
        self.canvas.bind(EButton1Down, None, self.move_button)
        self.canvas.bind(EButton1Down, None, self.eraser)
        self.canvas.bind(EButton1Down, None)

    def focus_monitor(self, value):
        if value:
            self.redraw_image()
            self.draw_buttons()

    def move_image(self, pos):
        self.move_active = not self.move_active
        self.draw_buttons()

    def set_exit(self, pos=(0,0)):
        appuifw.app.body = self.old_body
        self.canvas.bind(EButton1Down, None)
        self.canvas = None
        self.draw_img = None
        self.draw_buf = None
        self.mask = None
        appuifw.app.focus = None
        self.running = False

    def options_callback(self, pos):
        option = appuifw.popup_menu([u'Save', u'Zoom', u'About', u'Clear', u'Exit'],
                                    u'Options')
        if option == 0:
            self.save_callback()
        elif option == 1:
            zoom_levels = [u'50', u'100', u'200']
            zoom = appuifw.popup_menu(zoom_levels)
            if zoom is not None:
                self.IMAGE_ZOOM = int(zoom_levels[zoom])
                self.draw_buf = None
                self.draw_buf = Image.new((self.canvas.size[0]*100/self.IMAGE_ZOOM,
                                           self.canvas.size[1]*100/self.IMAGE_ZOOM))
                self.mask = None
                self.mask = Image.new((self.canvas.size[0]*100/self.IMAGE_ZOOM,
                                       self.canvas.size[1]*100/self.IMAGE_ZOOM),'L')
        elif option == 2:
            self.is_about_active = True
            self.show_about()
            return
        elif option == 3:
            self.reset_canvas()
        elif option == 4:
            self.set_exit()
            return
        self.redraw_image()
        self.draw_buttons()

    def show_about(self):
        appuifw.note(u"Scribble is Copyright (c) 2009 Nokia Corporation\nModified by Jose Sousa")
        self.redraw_image()
        self.draw_buttons()

    def clear_about_screen(self, pos=(0, 0)):
        self.canvas.bind(EButton1Up, None, ((0, 0), (self.x_max, self.y_max)))
        self.redraw_image()
        self.bind_palette = True
        self.draw_buttons()
        self.bind_buttons()
        self.about_active = False

    def mix_callback(self, pos):
        # The fill_color change in event_callback when mix_mode
        # changes
        self.mix_mode = (self.mix_mode+1)%3
        self.draw_buttons()

    def eraser_callback(self, pos):
        # The pen_width and fill_color change in event_callback when erase_mode
        # changes
        self.erase_mode = (self.erase_mode+1)%3
        self.draw_buttons()

    def save_callback(self):
        if not self.saving_file:
            self.saving_file = True
            save_dir = self.drive + u":\\data\\python\\"
            if not os.path.exists(save_dir):
                os.mkdir(save_dir)
            filename = save_dir + \
                   unicode(time.strftime("%d%m%Y%H%M%S", time.localtime())) + \
                   u".jpg"
            self.draw_img.save(filename, quality=100)
            appuifw.note(u"Saved :" + unicode(filename))
            self.redraw_image()
            self.saving_file = False
            self.draw_buttons()

    def set_BRUSH_COLOR(self, pos, color):
        self.BRUSH_COLOR = color
        self.new_color = color
        self.draw_buttons()

    def draw_and_bind_color(self, color):
        if self.orientation == 'portrait':
            self.top_left_x = (self.no_of_colors % (len(self.brush_history))) * self.color_box_width
            self.bottom_right_x = self.top_left_x + self.color_box_width
            self.top_left_y = self.y_max - self.toolbar_size
            self.bottom_right_y = self.top_left_y + (self.color_palette / 4)
        else:
            self.top_left_x = self.x_max - self.toolbar_size
            self.bottom_right_x = self.top_left_x + (self.color_palette / 4)
            self.top_left_y = (self.no_of_colors % (len(self.brush_history))) * self.color_box_width
            self.bottom_right_y = self.top_left_y + self.color_box_width

        self.top_left = (self.top_left_x, self.top_left_y)
        self.bottom_right = (self.bottom_right_x, self.bottom_right_y)
        # Draw the color rectangle and bind a function which sets the brush
        # color
        self.draw.rectangle((self.top_left, self.bottom_right),
                            fill=self.brush_history[color])
        if self.bind_palette:
            self.canvas.bind(EButton1Down,
                lambda pos: self.set_BRUSH_COLOR(pos, self.brush_history[color]),
                (self.top_left, self.bottom_right))
        self.no_of_colors += 1

    def apply_color(self, pos=(0,0)):
        self.BRUSH_COLOR = self.new_color
        self.brush_history[8] = self.brush_history[7]
        self.brush_history[7] = self.brush_history[6]
        self.brush_history[6] = self.brush_history[5]
        self.brush_history[5] = self.brush_history[4]
        self.brush_history[4] = self.brush_history[3]
        self.brush_history[3] = self.brush_history[2]
        self.brush_history[2] = self.brush_history[1]
        self.brush_history[1] = self.brush_history[0]
        self.brush_history[0] = self.new_color
        self.draw_buttons()

    def change_color(self,delta,component):
        new_value = self.new_color[component]+delta
        if new_value>255:
            new_value = 255
        if new_value<0:
            new_value = 0
        if component == 0:
            self.new_color = (new_value, self.new_color[1], self.new_color[2])
        elif component == 1:
            self.new_color = (self.new_color[0], new_value, self.new_color[2])
        else:
            self.new_color = (self.new_color[0], self.new_color[1], new_value)
        
        self.draw_buttons()

    def drag_red_callback(self,pos):
        if self.slider_id == 0:
            self.change_color(pos[0]-self.slider_prev_x,0)
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]
        else:
            self.slider_id = 0
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]

    def more_red_callback(self,pos=(0,0)):
        self.change_color(1,0)

    def less_red_callback(self,pos=(0,0)):
        self.change_color(-1,0)

    def drag_green_callback(self,pos):
        if self.slider_id == 1:
            self.change_color(pos[0]-self.slider_prev_x,1)
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]
        else:
            self.slider_id = 1
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]

    def more_green_callback(self,pos=(0,0)):
        self.change_color(1,1)

    def less_green_callback(self,pos=(0,0)):
        self.change_color(-1,1)

    def drag_blue_callback(self,pos):
        if self.slider_id == 2:
            self.change_color(pos[0]-self.slider_prev_x,2)
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]
        else:
            self.slider_id = 2
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]

    def more_blue_callback(self,pos=(0,0)):
        self.change_color(1,2)

    def less_blue_callback(self,pos=(0,0)):
        self.change_color(-1,2)

    def drag_width_callback(self,pos):
        if self.slider_id == 3:
            self.pen_width += (pos[0]-self.slider_prev_x)
            if self.pen_width < 1:
                self.pen_width = 1
            if self.pen_width > self.MAX_WIDTH:
                self.pen_width = self.MAX_WIDTH
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]
            self.draw_buttons()
        else:
            self.slider_id = 3
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]

    def more_width_callback(self, pos=(0,0)):
        if self.pen_width<self.MAX_WIDTH:
            self.pen_width += 1
            self.draw_buttons()

    def less_width_callback(self, pos=(0,0)):
        if self.pen_width>1:
            self.pen_width -= 1
            self.draw_buttons()

    def drag_mix_callback(self,pos):
        if self.slider_id == 4:
            self.mix_dist += pos[0]-self.slider_prev_x
            if self.mix_dist < 10:
                self.mix_dist = 10
            if self.mix_dist > self.MAX_MIX:
                self.mix_dist = self.MAX_MIX
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]
            self.draw_buttons()
        else:
            self.slider_id = 4
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]

    def more_mix_callback(self, pos=(0,0)):
         if self.mix_dist<self.MAX_MIX:
            self.mix_dist += 10
            self.draw_buttons()

    def less_mix_callback(self, pos=(0,0)):
        if self.mix_dist>10:
            self.mix_dist -= 10
            self.draw_buttons()

    def drag_opacity_callback(self,pos):
        if self.slider_id == 5:
            self.opacity_value += pos[0]-self.slider_prev_x
            if self.opacity_value < 0:
                self.opacity_value = 0
            if self.opacity_value > 255:
                self.opacity_value = 255
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]
            self.draw_buttons()
        else:
            self.slider_id = 5
            self.slider_prev_x = pos[0]
            self.slider_prev_y = pos[1]

    def more_opacity_callback(self, pos=(0,0)):
         if self.opacity_value<255:
            self.opacity_value += 1
            self.draw_buttons()

    def less_opacity_callback(self, pos=(0,0)):
        if self.opacity_value>0:
            self.opacity_value -= 1
            self.draw_buttons()

    def slider_reset(self, pos=(0,0)):
        self.slider_id = -1

    def draw_and_bind_button(self, area, callback):
        self.draw.rectangle(area, outline=self.BORDER_COLOR, width=2)
        self.canvas.bind(EButton1Up, callback, area)

    def draw_and_bind_slider(self, area, callback_list, color, value, min, max):
        less_button = ((area[0][0],area[0][1]),
                       (area[0][0]+(area[1][0]-area[0][0])/4,area[1][1]))
        more_button = ((area[0][0]+(area[1][0]-area[0][0])*3/4,area[0][1]),
                       (area[1][0],area[1][1]))
        slider_area = ((area[0][0]+(area[1][0]-area[0][0])/4,area[0][1]),
                       (area[0][0]+(area[1][0]-area[0][0])*3/4,area[1][1]))
        less_button_callback = callback_list[0]
        slide_callback = callback_list[1]
        more_button_callback = callback_list[2]
        # Create 'minus' button
        self.draw_and_bind_button(less_button, less_button_callback)
        self.draw.line( ((less_button[0][0]+(less_button[1][0]-less_button[0][0])*1/4, less_button[0][1]+(less_button[1][1]-less_button[0][1])*1/2),
                         (less_button[0][0]+(less_button[1][0]-less_button[0][0])*3/4, less_button[0][1]+(less_button[1][1]-less_button[0][1])*1/2)),
                        outline=self.BORDER_COLOR, width=1)
        # Create 'plus' button
        self.draw_and_bind_button(more_button, more_button_callback)
        self.draw.line( ((more_button[0][0]+(more_button[1][0]-more_button[0][0])*1/4, more_button[0][1]+(more_button[1][1]-more_button[0][1])*1/2),
                         (more_button[0][0]+(more_button[1][0]-more_button[0][0])*3/4, more_button[0][1]+(more_button[1][1]-more_button[0][1])*1/2)),
                        outline=self.BORDER_COLOR, width=1)
        self.draw.line( ((more_button[0][0]+(more_button[1][0]-more_button[0][0])*1/2, more_button[0][1]+(more_button[1][1]-more_button[0][1])*1/4),
                         (more_button[0][0]+(more_button[1][0]-more_button[0][0])*1/2, more_button[0][1]+(more_button[1][1]-more_button[0][1])*3/4)),
                        outline=self.BORDER_COLOR, width=1)
        # Create slider
        self.draw.rectangle( ((slider_area[0][0],slider_area[0][1]),
                              (slider_area[0][0]+(slider_area[1][0]-slider_area[0][0])*(value-min)/(max-min),slider_area[1][1])),
                              fill=color, width=2)
        self.canvas.bind(EDrag, slide_callback, slider_area)
        self.canvas.bind(EButton1Down, self.slider_reset, slider_area)

    def draw_color_picker(self):
        if self.orientation == 'landscape':
            rect = ((self.x_max-self.toolbar_size+self.color_palette*2/4, self.color_box_width*8),
                    (self.x_max-self.toolbar_size+self.color_palette*3/4, self.color_box_width*9))
        else:
            rect = ((self.color_box_width*8, self.y_max-self.toolbar_size+self.color_palette*2/4),
                    (self.color_box_width*9, self.y_max-self.toolbar_size+self.color_palette*3/4))
        self.draw.rectangle(rect, outline=self.MODE_ACTIVE, fill=self.new_color, width=2)
        
    def draw_and_bind_color_controls(self):
        if self.orientation == 'landscape':
            self.draw_and_bind_slider( ((self.x_max-self.toolbar_size+self.color_palette/4, 0),
                                        (self.x_max-self.toolbar_size+self.color_palette, self.color_box_width)),
                                        (self.less_red_callback,self.drag_red_callback,self.more_red_callback), (255,0,0), self.new_color[0], 0, 255)
            self.draw_and_bind_slider( ((self.x_max-self.toolbar_size+self.color_palette/4, self.color_box_width),
                                        (self.x_max-self.toolbar_size+self.color_palette, self.color_box_width*2)),
                                        (self.less_green_callback,self.drag_green_callback,self.more_green_callback), (0,255,0), self.new_color[1], 0, 255)
            self.draw_and_bind_slider( ((self.x_max-self.toolbar_size+self.color_palette/4, self.color_box_width*2),
                                        (self.x_max-self.toolbar_size+self.color_palette,self.color_box_width*3)),
                                        (self.less_blue_callback,self.drag_blue_callback,self.more_blue_callback), (0,0,255), self.new_color[2], 0, 255)
            self.draw_and_bind_slider( ((self.x_max-self.toolbar_size+self.color_palette/4,self.color_box_width*3),
                                        (self.x_max-self.toolbar_size+self.color_palette,self.color_box_width*4)),
                                        (self.less_width_callback,self.drag_width_callback,self.more_width_callback), (160,160,160), self.pen_width, 1, self.MAX_WIDTH)
            self.draw_and_bind_slider( ((self.x_max-self.toolbar_size+self.color_palette/4,self.color_box_width*4),
                                        (self.x_max-self.toolbar_size+self.color_palette,self.color_box_width*5)),
                                        (self.less_mix_callback,self.drag_mix_callback,self.more_mix_callback), (160,160,160), self.mix_dist, 10, self.MAX_MIX)
            self.draw_and_bind_slider( ((self.x_max-self.toolbar_size+self.color_palette/4,self.color_box_width*5),
                                        (self.x_max-self.toolbar_size+self.color_palette,self.color_box_width*6)),
                                        (self.less_opacity_callback,self.drag_opacity_callback,self.more_opacity_callback), (160,160,160), self.opacity_value, 0, 255)
            # active color
            self.draw.rectangle(((self.x_max-self.toolbar_size+self.color_palette/4, self.color_box_width*8),
                            (self.x_max-self.toolbar_size+self.color_palette*2/4, self.color_box_width*9)),
                            outline=self.BORDER_COLOR, fill=self.BRUSH_COLOR, width=2)
            # new color
            self.draw_color_picker()
                            
            self.canvas.bind(EButton1Up, self.apply_color, ((self.x_max-self.toolbar_size+self.color_palette*2/4, self.color_box_width*8),
                                                              (self.x_max-self.toolbar_size+self.color_palette*3/4, self.color_box_width*9))  )
        else:
            # portrait
            # sliders
            self.draw_and_bind_slider( ((0, self.y_max-self.toolbar_size+self.color_palette/4),
                                        (self.color_box_width*4, self.y_max-self.toolbar_size+self.color_palette*2/4)),
                                        (self.less_red_callback,self.drag_red_callback,self.more_red_callback), (255,0,0), self.new_color[0], 0, 255)
            self.draw_and_bind_slider( ((0, self.y_max-self.toolbar_size+self.color_palette*2/4),
                                        (self.color_box_width*4, self.y_max-self.toolbar_size+self.color_palette*3/4)),
                                        (self.less_green_callback,self.drag_green_callback,self.more_green_callback), (0,255,0), self.new_color[1], 0, 255)
            self.draw_and_bind_slider( ((0, self.y_max-self.toolbar_size+self.color_palette*3/4),
                                        (self.color_box_width*4, self.y_max-self.toolbar_size+self.color_palette)),
                                        (self.less_blue_callback,self.drag_blue_callback,self.more_blue_callback), (0,0,255), self.new_color[2], 0, 255)
            self.draw_and_bind_slider( ((self.color_box_width*4, self.y_max-self.toolbar_size+self.color_palette/4),
                                        (self.color_box_width*8, self.y_max-self.toolbar_size+self.color_palette*2/4)),
                                        (self.less_width_callback,self.drag_width_callback,self.more_width_callback), (160,160,160), self.pen_width, 1, self.MAX_WIDTH)
            self.draw_and_bind_slider( ((self.color_box_width*4, self.y_max-self.toolbar_size+self.color_palette*2/4),
                                        (self.color_box_width*8, self.y_max-self.toolbar_size+self.color_palette*3/4)),
                                        (self.less_mix_callback,self.drag_mix_callback,self.more_mix_callback), (160,160,160), self.mix_dist, 10, self.MAX_MIX)
            self.draw_and_bind_slider( ((self.color_box_width*4, self.y_max-self.toolbar_size+self.color_palette*3/4),
                                        (self.color_box_width*8, self.y_max-self.toolbar_size+self.color_palette)),
                                        (self.less_opacity_callback,self.drag_opacity_callback,self.more_opacity_callback), (160,160,160), self.opacity_value, 0, 255)
            # active color
            self.draw.rectangle(((self.color_box_width*8, self.y_max-self.toolbar_size+self.color_palette/4),
                            (self.color_box_width*9, self.y_max-self.toolbar_size+self.color_palette*2/4)),
                            outline=self.BORDER_COLOR, fill=self.BRUSH_COLOR, width=2)
            # new color
            self.draw_color_picker()

            self.canvas.bind(EButton1Up, self.apply_color, ((self.color_box_width*8, self.y_max-self.toolbar_size+self.color_palette*2/4),
                                                              (self.color_box_width*9, self.y_max-self.toolbar_size+self.color_palette*3/4)) )                

    def draw_palette(self):
        self.color_box_width = min(self.x_max, self.y_max) / (len(self.brush_history))
        self.no_of_colors = 0
        map(self.draw_and_bind_color, [0,1,2,3,4,5,6,7,8])
        self.draw_and_bind_color_controls();        
        if self.bind_palette:
            self.bind_palette = False

    def reset_canvas(self):
        self.draw_img.clear(self.BG_COLOR)
        self.prev_x = 0
        self.prev_y = 0
        self.erase_mode = 0
        self.mix_mode = 0
        self.canvas.clear(self.BG_COLOR)
        self.redraw_image()
        self.draw_buttons()

    def check_orientation(self):
        if not self.orientation_changed:
            self.orientation_changed = True
        else:
            self.orientation_changed = False
        self.x_max = self.canvas.size[0]
        self.y_max = self.canvas.size[1]

    def redraw_callback(self, rect):
        if self.about_active:
            self.canvas.blit(self.about_window)
        if rect == (0, 0, self.y_max, self.x_max) and \
                                                self.orientation == 'portrait':
            self.orientation = 'landscape'
            self.check_orientation()
        elif rect == (0, 0, self.y_max, self.x_max) and \
                                               self.orientation == 'landscape':
            self.orientation = 'portrait'
            self.check_orientation()

    def event_callback(self, event):
        if not event['type'] in [EButton1Up, EButton1Down, EDrag]:
            return

        if event['type'] == EButton1Up and self.is_about_active:
            # This check is for ignoring button up event generated when exiting
            # `About` menu option. The flag `is_about_active` is set when
            # `About` menu is active.
            self.is_about_active = False
            return
        
        if self.move_active:
            self.define_draw_area()
            if event['type'] == EButton1Down:
                self.prev_x = event['pos'][0]
                self.prev_y = event['pos'][1]
            elif event['type'] == EButton1Up and (event['pos'][0] > self.draw_area[0] and event['pos'][0] < self.draw_area[2] and
            event['pos'][1] > self.draw_area[1] and event['pos'][1] < self.draw_area[3]):
                self.redraw_image()
            elif event['type'] == EDrag:
                delta_x = self.IMAGE_POS[0]+(self.prev_x-event['pos'][0])*100/self.IMAGE_ZOOM
                if delta_x+(self.draw_area[2]-self.draw_area[0])*100/self.IMAGE_ZOOM>self.IMAGE_SIZE[0]:
                    delta_x = self.IMAGE_SIZE[0]-(self.draw_area[2]-self.draw_area[0])*100/self.IMAGE_ZOOM
                if delta_x<0:
                    delta_x = 0
                delta_y = self.IMAGE_POS[1]+(self.prev_y-event['pos'][1])*100/self.IMAGE_ZOOM
                if delta_y+(self.draw_area[3]-self.draw_area[1])*100/self.IMAGE_ZOOM>self.IMAGE_SIZE[1]:
                    delta_y = self.IMAGE_SIZE[1]-(self.draw_area[3]-self.draw_area[1])*100/self.IMAGE_ZOOM
                if delta_y<0:
                    delta_y = 0
                self.IMAGE_POS = (delta_x, delta_y)
                self.redraw_image()
                self.prev_x = event['pos'][0]
                self.prev_y = event['pos'][1]
            return
                
        if self.erase_mode == 1:
            pen_size = self.pen_width * 2
            outline_color = self.BG_COLOR
            fill_color = self.BG_COLOR
        elif self.erase_mode == 2:
            pen_size = 1;
            if self.draw_img == None or (event['pos'][0] < max(pen_size*self.IMAGE_ZOOM/200,1) and event['pos'][0] > min(self.draw_area[0], (self.IMAGE_SIZE[0]-self.IMAGE_POS[0])*100/self.IMAGE_ZOOM) - max(pen_size*self.IMAGE_ZOOM/200,1) and
            event['pos'][1] < max(pen_size*self.IMAGE_ZOOM/200,1) and event['pos'][1] > min(self.draw_area[1], (self.IMAGE_SIZE[1]-self.IMAGE_POS[1])*100/self.IMAGE_ZOOM) - max(pen_size*self.IMAGE_ZOOM/200,1)):
                return
            self.new_color = self.draw_img.getpixel((self.IMAGE_POS[0]+event['pos'][0]*100/self.IMAGE_ZOOM,self.IMAGE_POS[1]+event['pos'][1]*100/self.IMAGE_ZOOM))[0]
            self.draw_color_picker()
            return
        elif self.mix_mode == 1:
            if self.draw_img == None:
                return
            pen_size = self.pen_width
            if event['type'] == EButton1Down:
                self.mix_init = self.draw_img.getpixel((self.IMAGE_POS[0]+event['pos'][0]*100/self.IMAGE_ZOOM,self.IMAGE_POS[1]+event['pos'][1]*100/self.IMAGE_ZOOM))[0]
                self.mix_counter = 1
                outline_color = self.mix_init
                fill_color = outline_color
            else:
                red_comp   = 256+self.mix_init[0]+((self.BRUSH_COLOR[0]-self.mix_init[0])*self.mix_counter)/self.mix_dist
                green_comp = 256+self.mix_init[1]+((self.BRUSH_COLOR[1]-self.mix_init[1])*self.mix_counter)/self.mix_dist
                blue_comp  = 256+self.mix_init[2]+((self.BRUSH_COLOR[2]-self.mix_init[2])*self.mix_counter)/self.mix_dist
                outline_color = (red_comp%256,green_comp%256,blue_comp%256)
                fill_color = outline_color
        elif self.mix_mode==2:
            if self.draw_img == None:
                return
            pen_size = self.pen_width
            if event['type'] == EButton1Down:
                self.mix_init = self.draw_img.getpixel((self.IMAGE_POS[0]+event['pos'][0]*100/self.IMAGE_ZOOM,self.IMAGE_POS[1]+event['pos'][1]*100/self.IMAGE_ZOOM))[0]
                self.draw_buttons()
                self.mix_counter = 1
            else:
                color = self.draw_img.getpixel((self.IMAGE_POS[0]+event['pos'][0]*100/self.IMAGE_ZOOM,self.IMAGE_POS[1]+event['pos'][1]*100/self.IMAGE_ZOOM))[0]
                red_comp   = 256+self.mix_init[0]+((color[0]-self.mix_init[0])*self.mix_counter)/self.mix_dist
                green_comp = 256+self.mix_init[1]+((color[1]-self.mix_init[1])*self.mix_counter)/self.mix_dist
                blue_comp  = 256+self.mix_init[2]+((color[2]-self.mix_init[2])*self.mix_counter)/self.mix_dist
                self.mix_init = (red_comp%256,green_comp%256,blue_comp%256)
                self.mix_counter = 1
            outline_color = self.mix_init
            fill_color = outline_color
        else:
            pen_size = self.pen_width
            outline_color = self.BRUSH_COLOR
            fill_color = self.BRUSH_COLOR
        
        # Ignore the touch events in the region where buttons are drawn or if
        # about screen is active or if they are outside the image area
        if (event['pos'][0] < self.draw_area[0]+max(pen_size*self.IMAGE_ZOOM/200,1) or event['pos'][0] > min(self.draw_area[2], (self.IMAGE_SIZE[0]-self.IMAGE_POS[0])*self.IMAGE_ZOOM/100) - max(pen_size*self.IMAGE_ZOOM/200,1) or
            event['pos'][1] < self.draw_area[1]+max(pen_size*self.IMAGE_ZOOM/200,1) or event['pos'][1] > min(self.draw_area[3], (self.IMAGE_SIZE[1]-self.IMAGE_POS[1])*self.IMAGE_ZOOM/100) - max(pen_size*self.IMAGE_ZOOM/200,1)):
            return

        image_rect = (self.IMAGE_POS,
                      (min(self.IMAGE_POS[0]+(self.draw_area[2]-self.draw_area[0])*100/self.IMAGE_ZOOM,self.IMAGE_SIZE[0]),
                      min(self.IMAGE_POS[1]+(self.draw_area[3]-self.draw_area[1])*100/self.IMAGE_ZOOM,self.IMAGE_SIZE[1]) ) )
        buffer_rect = ((0,0),
                      (min((self.draw_area[2]-self.draw_area[0])*100/self.IMAGE_ZOOM,self.IMAGE_SIZE[0]),
                      min((self.draw_area[3]-self.draw_area[1])*100/self.IMAGE_ZOOM,self.IMAGE_SIZE[1]) ) )

        if event['type'] in [EButton1Down, EButton1Up]:
            self.draw.point((event['pos'][0], event['pos'][1]),
                            outline=outline_color, width=max(pen_size*self.IMAGE_ZOOM/100,1), fill=fill_color)
            if self.opacity_value == 255:
                self.draw_img.point((self.IMAGE_POS[0]+event['pos'][0]*100/self.IMAGE_ZOOM, self.IMAGE_POS[1]+event['pos'][1]*100/self.IMAGE_ZOOM),
                                    outline=outline_color, width=pen_size, fill=fill_color)
            else:
                if event['type'] == EButton1Down:
                    self.draw_buf.blit(self.draw_img,source=image_rect,target=buffer_rect, scale=0)
                    self.opacity_active = True
                else:
                    self.draw_buf.point((event['pos'][0]*100/self.IMAGE_ZOOM, event['pos'][1]*100/self.IMAGE_ZOOM),
                                        outline=outline_color, width=pen_size, fill=fill_color)
                    self.mask.point((event['pos'][0]*100/self.IMAGE_ZOOM, event['pos'][1]*100/self.IMAGE_ZOOM),
                                    outline=(self.opacity_value,self.opacity_value,self.opacity_value), width=pen_size,
                                    fill=(self.opacity_value,self.opacity_value,self.opacity_value))
                    self.draw_img.blit(self.draw_buf, mask=self.mask, source=buffer_rect, target=image_rect)
                    self.redraw_image()
                    self.mask.clear(0)
                    self.opacity_active = False
                    self.draw_buttons()
        elif event['type'] == EDrag:
            rect = (self.prev_x, self.prev_y, event['pos'][0], event['pos'][1])
            redraw_rect = list(rect)
            # Ensure that the prev_x and prev_y co-ordinates are above the
            # current co-ordinates. This way we can use prev_x and prev_y as
            # the top left corner and the current co-ordinates as the bottom
            # right corner of the rect to be passed to begin_redraw.
            if redraw_rect[0] > redraw_rect[2]:
                redraw_rect[0], redraw_rect[2] = redraw_rect[2], redraw_rect[0]
            if redraw_rect[1] > redraw_rect[3]:
                redraw_rect[1], redraw_rect[3] = redraw_rect[3], redraw_rect[1]
            self.canvas.begin_redraw((redraw_rect[0] - pen_size,
                                      redraw_rect[1] - pen_size,
                                      redraw_rect[2] + pen_size,
                                      redraw_rect[3] + pen_size))
            self.draw.line(rect, outline=outline_color, width=max(pen_size*self.IMAGE_ZOOM/100,1), fill=fill_color)
            self.canvas.end_redraw()
            if self.opacity_value == 255:
                self.draw_img.line( (rect[0]*100/self.IMAGE_ZOOM+self.IMAGE_POS[0],rect[1]*100/self.IMAGE_ZOOM+self.IMAGE_POS[1],
                                     rect[2]*100/self.IMAGE_ZOOM+self.IMAGE_POS[0],rect[3]*100/self.IMAGE_ZOOM+self.IMAGE_POS[1]),
                                     outline=outline_color, width=pen_size, fill=fill_color)
            else:
                self.draw_buf.line((rect[0]*100/self.IMAGE_ZOOM,rect[1]*100/self.IMAGE_ZOOM,
                                    rect[2]*100/self.IMAGE_ZOOM,rect[3]*100/self.IMAGE_ZOOM),
                                    outline=outline_color, width=pen_size, fill=fill_color)
                self.mask.line((rect[0]*100/self.IMAGE_ZOOM,rect[1]*100/self.IMAGE_ZOOM,
                                rect[2]*100/self.IMAGE_ZOOM,rect[3]*100/self.IMAGE_ZOOM),
                                outline=(self.opacity_value,self.opacity_value,self.opacity_value),
                                fill=(self.opacity_value,self.opacity_value,self.opacity_value), width=pen_size)
            if self.mix_mode != 0:
                self.mix_counter += 1
                if self.mix_counter>self.mix_dist:
                    self.mix_counter = self.mix_dist
        
        self.prev_x = event['pos'][0]
        self.prev_y = event['pos'][1]

    def run(self):
        while self.running:
            e32.ao_sleep(0.01)
            if self.orientation_changed:
                self.draw_buf = None
                self.draw_buf = Image.new((self.canvas.size[0]*100/self.IMAGE_ZOOM,
                                           self.canvas.size[1]*100/self.IMAGE_ZOOM))
                self.mask = None
                self.mask = Image.new((self.canvas.size[0]*100/self.IMAGE_ZOOM,
                                       self.canvas.size[1]*100/self.IMAGE_ZOOM),'L')
                self.redraw_image()
                self.clear_button_bindings()
                if self.about_active:
                    self.clear_about_screen()
                self.bind_palette = True
                self.draw_buttons()
                self.bind_buttons()
                self.orientation_changed = False

        self.quit()

    def quit(self):
        appuifw.app.exit_key_handler = None
        self.running = False

if not appuifw.touch_enabled():
    appuifw.note(u"This application only works on devices that support " +
                 u"touch input")
else:
    d = PaintApp()
    d.run()
