#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 0.8.3 on Thu Aug 09 23:03:17 2018
#

import wx
import wx.grid
import sys
import pyembroidery
from pyembroidery.CsvWriter import get_common_name_dictionary
from pyembroidery.CsvReader import get_command_dictionary

USE_BUFFERED_DC = True


class EmbroideryView(wx.Panel):
    def __init__(self, *args, **kwds):
        self.draw_data = None
        self.emb_pattern = None
        self.scale = 1
        self.translate_x = 0
        self.translate_y = 0
        self.buffer = 0.1
        self._Buffer = None
        self.current_stitch = -1
        self.selected_point = None
        self.drag_point = None
        self.name_dict = get_common_name_dictionary()

        # begin wxGlade: EmbroideryView.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Panel.__init__(self, *args, **kwds)

        # end wxGlade
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase)

        self.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_press)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_double_click)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_mouse_down)

        # OnSize called to make sure the buffer is initialized.
        # This might result in OnSize getting called twice on some
        # platforms at initialization, but little harm done.
        self.on_size(None)
        self.paint_count = 0

    def on_mouse_move(self, event):
        if self.drag_point is None:
            return
        mod_stitch = self.emb_pattern.stitches[self.drag_point]
        position = self.get_pattern_point(event.GetPosition())
        mod_stitch[0] = position[0]
        mod_stitch[1] = position[1]
        self.update_drawing()

    def on_mouse_down(self, event):
        self.SetFocus()
        if self.emb_pattern is None:
            return
        position = event.GetPosition()
        nearest = self.get_nearest_point(position)
        if nearest[1] > 25:
            event.Skip()
            self.drag_point = None
            return
        best_index = nearest[0]
        self.drag_point = best_index
        self.selected_point = best_index

    def on_mouse_up(self, event):
        self.drag_point = None
        self.update_affines()
        self.update_drawing()

    def on_left_double_click(self, event):
        self.clicked_position = event.GetPosition()
        nearest = self.get_nearest_point(self.clicked_position)
        if nearest[0] is None:
            position = self.get_pattern_point(self.clicked_position)
            stitches = self.emb_pattern.stitches
            stitches.append([position[0], position[1], pyembroidery.STITCH])
            self.selected_point = 0
            self.update_affines()
            self.update_drawing()
            return
        if nearest[1] > 25:
            if self.selected_point is None:
                return
            stitches = self.emb_pattern.stitches
            stitch = stitches[self.selected_point]
            new_stitch = stitch[:]
            position = self.get_pattern_point(self.clicked_position)
            new_stitch[0] = position[0]
            new_stitch[1] = position[1]
            stitches.insert(self.selected_point + 1, new_stitch)
            self.selected_point += 1
            self.update_affines()
            self.update_drawing()
            return
        best_index = nearest[0]
        stitches = self.emb_pattern.stitches
        stitch = stitches[best_index]
        stitches.insert(best_index, stitch[:])
        self.selected_point = best_index
        self.update_drawing()

    def on_right_mouse_down(self, event):
        self.clicked_position = event.GetPosition()
        nearest = self.get_nearest_point(self.clicked_position)
        if nearest[1] > 25:
            event.Skip()
            return
        menu = wx.Menu()
        menu_item = menu.Append(wx.ID_ANY, "Delete", "")
        self.Bind(wx.EVT_MENU, self.on_menu_delete, menu_item)
        menu_item = menu.Append(wx.ID_ANY, "Duplicate", "")
        self.Bind(wx.EVT_MENU, self.on_menu_duplicate, menu_item)
        self.PopupMenu(menu)
        menu.Destroy()

    def on_menu_delete(self, event):
        best_index = self.get_nearest_point(self.clicked_position)[0]
        stitches = self.emb_pattern.stitches
        del stitches[best_index]
        self.selected_point = None
        self.update_drawing()

    def on_menu_duplicate(self, event):
        best_index = self.get_nearest_point(self.clicked_position)[0]
        stitches = self.emb_pattern.stitches
        stitch = stitches[best_index]
        stitches.insert(best_index, stitch[:])
        self.selected_point = best_index
        self.update_drawing()

    def on_key_press(self, event):
        keycode = event.GetKeyCode()
        stitch_max = len(self.emb_pattern.stitches)
        if keycode in [68, wx.WXK_RIGHT, wx.WXK_NUMPAD6]:
            if self.selected_point is None:
                self.selected_point = 0
            else:
                self.selected_point += 1
            if self.selected_point >= stitch_max:
                self.selected_point = stitch_max - 1
            self.update_drawing()
        elif keycode in [65, wx.WXK_LEFT, wx.WXK_NUMPAD4]:
            if self.selected_point is None:
                self.selected_point = stitch_max - 1
            else:
                self.selected_point -= 1
            if self.selected_point < 0:
                self.selected_point = 0
            self.update_drawing()
        elif keycode in [127]:
            position = self.selected_point
            if position is None:
                return
            stitches = self.emb_pattern.stitches
            del stitches[position]
            stitch_max = len(self.emb_pattern.stitches)
            if self.selected_point >= stitch_max:
                self.selected_point = stitch_max - 1
            if stitch_max == 0:
                self.selected_point = None
            self.update_drawing()

    def on_draw(self, dc):
        dc.SetBackground(wx.Brush("Grey"))
        dc.Clear()
        if self.emb_pattern is None:
            return
        scale = self.scale
        tran_x = self.translate_x
        tran_y = self.translate_y
        draw_data = []
        for color in self.emb_pattern.get_as_colorblocks():
            lines = []
            last_x = None
            last_y = None
            for i, stitch in enumerate(color[0]):
                current_x = stitch[0] + tran_x
                current_y = stitch[1] + tran_y
                if last_x is not None:
                    lines.append([last_x * scale, last_y * scale, current_x * scale, current_y * scale])
                last_x = current_x
                last_y = current_y
            thread = color[1]
            draw_data.append(((thread.get_red(), thread.get_green(), thread.get_blue()), lines))

        current_stitch = self.current_stitch
        # Here's the actual drawing code.

        if current_stitch == -1:
            for drawElements in draw_data:
                pen = wx.Pen(drawElements[0])
                pen.SetWidth(3)
                dc.SetPen(pen)
                dc.DrawLineList(drawElements[1])
        else:
            count = 0
            count_range = 0
            for drawElements in draw_data:
                pen = wx.Pen(drawElements[0])
                pen.SetWidth(5)
                dc.SetPen(pen)
                count_range += len(drawElements[1])
                if current_stitch < count_range:
                    dif = current_stitch - count
                    segments = drawElements[1]
                    subsegs = segments[:dif]
                    dc.DrawLineList(subsegs)
                    break
                else:
                    dc.DrawLineList(drawElements[1])
                count = count_range
        # dc.SetBrush(wx.Brush("Blue"))
        dc.GetPen().SetWidth(1)
        # for stitch in self.emb_pattern.stitches:
        # dc.DrawCircle((tran_x + stitch[0]) * scale, (tran_y + stitch[1]) * scale, scale * 3)

        if self.selected_point is not None:
            mod_stitch = self.emb_pattern.stitches[self.selected_point]
            name = self.name_dict[mod_stitch[2]] + " " + str(self.selected_point)
            dc.DrawText(name, 25, 25)
            dc.SetBrush(wx.Brush("Green"))
            dc.DrawCircle((tran_x + mod_stitch[0]) * scale, (tran_y + mod_stitch[1]) * scale, scale * 3)

    def on_paint(self, event):
        # All that is needed here is to draw the buffer to screen
        if USE_BUFFERED_DC:
            dc = wx.BufferedPaintDC(self, self._Buffer)
        else:
            dc = wx.PaintDC(self)
            dc.DrawBitmap(self._Buffer, 0, 0)

    def update_affine(self, width, height):
        extends = self.emb_pattern.extends()
        min_x = min(extends[0], 50)
        min_y = min(extends[1], -50)
        max_x = max(extends[2], 50)
        max_y = max(extends[3], -50)

        embroidery_width = (max_x - min_x) + (width * self.buffer)
        embroidery_height = (max_y - min_y) + (height * self.buffer)
        scale_x = float(width) / embroidery_width
        scale_y = float(height) / embroidery_height
        self.scale = min(scale_x, scale_y)
        self.translate_x = -min_x + (width * self.buffer) / 2
        self.translate_y = -min_y + (height * self.buffer) / 2

    def update_affines(self):
        Size = self.ClientSize
        try:
            self.update_affine(Size[0], Size[1])
        except (AttributeError, TypeError):
            pass

    def on_size(self, event):
        self.update_affines()
        Size = self.ClientSize
        self._Buffer = wx.Bitmap(*Size)
        self.update_drawing()

    def on_erase(self, event):
        pass

    def update_drawing(self):
        """
        This would get called if the drawing needed to change, for whatever reason.

        The idea here is that the drawing is based on some data generated
        elsewhere in the system. If that data changes, the drawing needs to
        be updated.

        This code re-draws the buffer, then calls Update, which forces a paint event.
        """
        dc = wx.MemoryDC()
        dc.SelectObject(self._Buffer)
        self.on_draw(dc)
        del dc  # need to get rid of the MemoryDC before Update() is called.
        self.Refresh()
        self.Update()

    def set_design(self, set_design):
        self.emb_pattern = set_design
        self.update_drawing()

    def get_pattern_point(self, position):
        px = position[0]
        py = position[1]
        px /= self.scale
        py /= self.scale
        px -= self.translate_x
        py -= self.translate_y
        px = round(px / 2.5) * 2.5
        py = round(py / 2.5) * 2.5
        return px, py

    @staticmethod
    def distance_sq(p0, p1):
        dx = p0[0] - p1[0]
        dy = p0[1] - p1[1]
        dx *= dx
        dy *= dy
        return dx + dy

    def get_nearest_point(self, position):
        scene_x = position[0]
        scene_y = position[1]
        scene_x /= self.scale
        scene_y /= self.scale
        scene_x -= self.translate_x
        scene_y -= self.translate_y
        click_point = (scene_x, scene_y)
        best_point = None
        best_index = None
        best_distance = sys.maxint
        for i, stitch in enumerate(self.emb_pattern.stitches):
            distance = self.distance_sq(click_point, stitch)
            if best_point is None or distance < best_distance or (
                    distance == best_distance and self.selected_point == i):
                best_point = stitch
                best_distance = distance
                best_index = i
        return best_index, best_distance, best_point


# end of class EmbroideryView


class SimulatorView(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: SimulatorView.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((845, 605))
        self.stitch_slider = wx.Slider(self, wx.ID_ANY, 0, 0, 10)
        self.Bind(wx.EVT_SCROLL_CHANGED, self.on_slider_changed, self.stitch_slider)
        self.canvas = EmbroideryView(self, wx.ID_ANY)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Menu Bar
        self.frame_menubar = wx.MenuBar()

        wxglade_tmp_menu = wx.Menu()
        menu_start = wxglade_tmp_menu.Append(wx.ID_ANY, "Start", "")
        self.Bind(wx.EVT_MENU, self.on_menu_start, menu_start)
        self.menu_start = menu_start
        menu_backwards = wxglade_tmp_menu.Append(wx.ID_ANY, "Backwards", "", wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.on_menu_backwards, menu_backwards)
        menu_track = wxglade_tmp_menu.Append(wx.ID_ANY, "Track", "", wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.on_menu_track, menu_track)

        self.frame_menubar.Append(wxglade_tmp_menu, "Options")
        self.SetMenuBar(self.frame_menubar)
        # Menu Bar end

        self.__set_properties()
        self.__do_layout()
        # end wxGlade
        self.design = None
        self.track = False
        self.forwards = True
        self.timer = None

    def on_slider_changed(self, event):
        self.canvas.current_stitch = event.GetPosition()
        self.canvas.update_drawing()

    def on_menu_start(self, event):
        if not self.timer:
            self.timer = wx.PyTimer(self.update_tick)
            self.timer.Start(30)
            self.menu_start.SetItemLabel("Stop")
        else:
            self.timer.Stop()
            self.timer = None
            self.menu_start.SetItemLabel("Start")

    def on_menu_track(self, event):
        self.track = not self.track

    def on_menu_forwards(self, event):
        self.forwards = True

    def on_menu_backwards(self, event):
        self.forwards = not self.forwards

    def on_close(self, event):
        if self.timer is not None:
            self.timer.Stop()
        event.Skip()

    def update_tick(self):
        if self.forwards:
            self.increment_stitch()
        else:
            self.decrement_stitch()
        self.stitch_slider.SetValue(self.canvas.current_stitch)
        self.canvas.update_drawing()

    def OnErase(self, event):
        pass

    def __set_properties(self):
        # begin wxGlade: SimulatorView.__set_properties
        self.SetTitle("Simulator")
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: SimulatorView.__do_layout
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_3.Add(self.stitch_slider, 0, wx.EXPAND, 0)
        sizer_3.Add(self.canvas, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_3)
        self.Layout()
        # end wxGlade

    def set_design(self, set_design):
        self.design = set_design
        self.canvas.set_design(set_design)
        self.stitch_slider.SetMax(len(self.canvas.emb_pattern.stitches))
        self.stitch_slider.SetMin(0)

    def decrement_stitch(self):
        self.canvas.current_stitch -= 1
        if self.canvas.current_stitch < 0:
            self.canvas.current_stitch = len(self.canvas.emb_pattern.stitches)

    def increment_stitch(self):
        self.canvas.current_stitch += 1
        if self.canvas.current_stitch > len(self.canvas.emb_pattern.stitches):
            self.canvas.current_stitch = 0

    def rebuild_draw_data(self):
        draw_data = []
        extends = self.canvas.emb_pattern.get_extends()
        for color in self.canvas.emb_pattern.get_as_stitchblock():
            lines = []
            last_x = None
            last_y = None
            for stitch in color[0]:
                current_x = stitch[0] - extends[0]
                current_y = stitch[1] - extends[1]
                if last_x is not None:
                    lines.append([last_x, last_y, current_x, current_y])
                last_x = current_x
                last_y = current_y
            thread = color[1]
            draw_data.append(((thread.get_red(), thread.get_green(), thread.get_blue()), lines))
        return draw_data

    def scale_draw_data(self, width, height):
        draw_data = self.rebuild_draw_data()
        return self.get_scaled_draw_data(draw_data, width, height)

    def get_scaled_draw_data(self, data, width, height):
        extends = self.canvas.emb_pattern.get_extends()
        new_data = []
        embroidery_width = extends[2] - extends[0]
        embroidery_height = extends[3] - extends[1]
        scale_x = float(width) / embroidery_width
        scale_y = float(height) / embroidery_height
        scale = min(scale_x, scale_y)
        for element in data:
            scaled_lines = []
            unscaled_lines = element[1]
            for e in unscaled_lines:
                scaled_lines.append([scale * e[0], scale * e[1], scale * e[2], scale * e[3]])
            new_data.append((element[0], scaled_lines))
        return new_data


# end of class SimulatorView


class StitchEditor(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: StitchEditor.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.design = None
        self.SetSize((597, 627))

        self.grid = wx.grid.Grid(self, wx.ID_ANY, size=(1, 1))
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK,
                       self.show_popup_menu_label)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK,
                       self.show_popup_menu_cell)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_grid_change)

        self.__set_properties()
        self.__do_layout()
        self.last_event = None
        self.command_menu = {}
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: StitchEditor.__set_properties
        self.SetTitle("Stitch Editor")
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: StitchEditor.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.grid, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def on_grid_change(self, event):
        row = event.GetRow()
        col = event.GetCol()
        value = self.grid.GetCellValue(row, col)
        stitches = self.design.emb_pattern.stitches
        stitch = stitches[row]

        if col == -1:
            return
        elif col == 0:
            command_dict = get_command_dictionary()
            command = command_dict[value]
            stitch[2] = command
        elif col == 1:
            stitch[0] = float(value)
        elif col == 2:
            stitch[1] = float(value)

    def show_popup_menu_label(self, event):
        self.last_event = event
        menu = wx.Menu()

        menu_item = menu.Append(wx.ID_ANY, "Delete", "")
        self.Bind(wx.EVT_MENU, self.on_menu_delete, menu_item)

        menu_item = menu.Append(wx.ID_ANY, "Duplicate", "")
        self.Bind(wx.EVT_MENU, self.on_menu_duplicate, menu_item)

        self.PopupMenu(menu)
        menu.Destroy()

    def show_popup_menu_cell(self, event):
        self.last_event = event
        col = event.GetCol()
        if col != 0:
            return
        row = event.GetRow()
        stitches = self.design.stitches
        stitch = stitches[row]

        self.last_event = event
        menu = wx.Menu()
        name_dict = get_common_name_dictionary()

        for the_key, the_value in name_dict.items():
            menu_item = menu.Append(the_key, the_value, the_value)
            self.Bind(wx.EVT_MENU, self.on_menu_cell_key, menu_item)
        self.PopupMenu(menu)
        menu.Destroy()

    def on_menu_cell_key(self, event):
        col = self.last_event.GetCol()
        row = self.last_event.GetRow()
        stitches = self.design.stitches
        stitch = stitches[row]
        name_dict = get_common_name_dictionary()
        command = event.GetId()
        command_name = name_dict[command]
        stitch[2] = command
        self.grid.SetCellValue(row, col, command_name)

    def on_menu_delete(self, event):
        stitches = self.design.stitches
        position = self.last_event.GetRow()
        del stitches[position]
        self.grid.DeleteRows(position)

    def on_menu_duplicate(self, event):
        stitches = self.design.stitches
        position = self.last_event.GetRow()
        stitch = stitches[position]
        stitches.insert(position, stitch[:])
        self.grid.InsertRows(position)
        common_dict = get_common_name_dictionary()
        common_name = common_dict[stitch[2]]
        self.grid.SetCellValue(position, 0, common_name)
        self.grid.SetCellValue(position, 1, str(stitch[0]))
        self.grid.SetCellValue(position, 2, str(stitch[1]))

    def set_design(self, set_design):
        self.design = set_design
        max = len(self.design.stitches)
        self.grid.CreateGrid(max, 3)
        self.grid.EnableDragColSize(0)
        self.grid.EnableDragRowSize(0)
        self.grid.EnableDragGridSize(0)
        self.grid.SetColLabelValue(0, "Command")
        self.grid.SetColLabelValue(1, "X")
        self.grid.SetColLabelValue(2, "Y")

        common_dict = get_common_name_dictionary()
        for i, stitch in enumerate(self.design.stitches):
            common_name = common_dict[stitch[2]]
            self.grid.SetCellValue(i, 0, common_name)
            self.grid.SetCellValue(i, 1, str(stitch[0]))
            self.grid.SetCellValue(i, 2, str(stitch[1]))

    # end of class StitchEditor


class ColorEmbroidery(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ColorEmbroidery.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Panel.__init__(self, *args, **kwds)
        self.SetSize((400, 300))
        # self.tree_ctrl_1 = wx.TreeCtrl(self, wx.ID_ANY)
        # This was intended to display color information.
        self.canvas = EmbroideryView(self, wx.ID_ANY)

        self.__do_layout()
        self.design = None
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ColorEmbroidery.__do_layout
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        # sizer_6.Add(self.tree_ctrl_1, 1, wx.EXPAND, 0)
        sizer_6.Add(self.canvas, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_6)
        self.Layout()
        # end wxGlade

    def set_design(self, set_design):
        self.design = set_design
        self.canvas.set_design(self.design)


# end of class ColorEmbroidery
class GuiMain(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: GuiMain.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((697, 552))
        self.main_notebook = wx.Notebook(self, wx.ID_ANY)
        self.Bind(wx.EVT_BOOKCTRL_PAGE_CHANGED, self.on_page_changed, self.main_notebook)

        # Menu Bar
        self.menubar = wx.MenuBar()
        wxglade_tmp_menu = wx.Menu()
        menu_import = wxglade_tmp_menu.Append(wx.ID_ANY, "Import", "")
        self.Bind(wx.EVT_MENU, self.on_menu_import, menu_import)

        menu_export = wxglade_tmp_menu.Append(wx.ID_ANY, "Export", "")
        self.Bind(wx.EVT_MENU, self.on_menu_export, menu_export)
        self.menubar.Append(wxglade_tmp_menu, "File")
        wxglade_tmp_menu = wx.Menu()
        menu_stitch_edit = wxglade_tmp_menu.Append(wx.ID_ANY, "Stitch Edit", "")
        self.Bind(wx.EVT_MENU, self.on_menu_stitch_edit, menu_stitch_edit)

        self.menubar.Append(wxglade_tmp_menu, "Edit")
        wxglade_tmp_menu = wx.Menu()
        menu_simulate = wxglade_tmp_menu.Append(wx.ID_ANY, "Simulate", "")
        self.Bind(wx.EVT_MENU, self.on_menu_simulate, menu_simulate)
        self.menubar.Append(wxglade_tmp_menu, "View")
        self.SetMenuBar(self.menubar)
        # Menu Bar end

        self.__set_properties()
        # self.__do_layout()
        # end wxGlade
        self.designs = []
        self.focused_design = None

        self.Bind(wx.EVT_DROP_FILES, self.on_drop_file)

    def on_drop_file(self, event):
        for pathname in event.GetFiles():
            pattern = pyembroidery.read(str(pathname))
            pattern.extras["filename"] = pathname
            self.add_embroidery(pattern)

    def on_page_changed(self, event):
        page = self.main_notebook.CurrentPage
        if isinstance(page, ColorEmbroidery):
            self.focused_design = page.design

    def on_menu_stitch_edit(self, event):
        stitch_list = StitchEditor(None, wx.ID_ANY, "")
        stitch_list.set_design(self.focused_design)
        stitch_list.Show()

    def on_menu_import(self, event):
        files = ""
        for format in pyembroidery.supported_formats():
            try:
                if format["reader"] is not None:
                    files += "*." + format["extension"] + ";"
            except KeyError:
                pass

        with wx.FileDialog(self, "Open Embroidery", wildcard="Embroidery Files (" + files + ")",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind
            pathname = fileDialog.GetPath()
            pattern = pyembroidery.read(str(pathname))
            pattern.extras["filename"] = pathname
            self.add_embroidery(pattern)

    def on_menu_export(self, event):
        files = ""
        for format in pyembroidery.supported_formats():
            try:
                if format["writer"] is not None:
                    files += format["description"] + "(*." + format["extension"] + ")|*." + format[
                        "extension"] + "|"
            except KeyError:
                pass

        with wx.FileDialog(self, "Save Embroidery", wildcard=files[:-1],
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            pyembroidery.write(self.focused_design.emb_pattern, str(pathname))

    def on_menu_simulate(self, event):
        simulator = SimulatorView(None, wx.ID_ANY, "")
        simulator.set_design(self.focused_design)
        simulator.Show()

    def add_embroidery(self, embroidery):
        self.designs.append(embroidery)
        page_sizer = wx.BoxSizer(wx.HORIZONTAL)
        embrodery_panel = ColorEmbroidery(self.main_notebook, wx.ID_ANY)
        embrodery_panel.set_design(embroidery)
        self.main_notebook.AddPage(embrodery_panel, embroidery.extras['filename'])
        page_sizer.Add(self.main_notebook, 1, wx.EXPAND, 0)
        page = self.main_notebook.CurrentPage
        if isinstance(page, ColorEmbroidery):
            self.focused_design = page.design
        self.Layout()

    def __set_properties(self):
        # begin wxGlade: GuiMain.__set_properties
        self.SetTitle("EmbroidepyEditor")
        self.DragAcceptFiles(True)
        # end wxGlade


# end of class GuiMain

class Embroidepy(wx.App):
    def OnInit(self):
        self.main_editor = GuiMain(None, wx.ID_ANY, "")
        self.SetTopWindow(self.main_editor)
        self.main_editor.Show()
        return True

    def add_embroidery(self, embroidery):
        self.main_editor.add_embroidery(embroidery)

    # end of class Embroidepy


if __name__ == "__main__":
    filename = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    embroiderpy = Embroidepy(0)
    if filename is not None:
        emb_pattern = pyembroidery.read(filename)
        emb_pattern.extras["filename"] = filename
        embroiderpy.add_embroidery(emb_pattern)
    embroiderpy.MainLoop()
