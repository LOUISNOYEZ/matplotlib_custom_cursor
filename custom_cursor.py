import math
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.transforms import nonsingular
import numpy as np

class custom_cursor:
    """ Curstom cursor features:
        - Crosshair with data display, toggle with <left double click>
        - Add and remove data axis labeling with <left simple click>
        - Create new label with <right click>
        - Snap to point with <shift>
        - Create horizontal guide with <space>
        - Create horizontal guide with <alt-space>
        - Clear guides with <enter>
    """

    def __init__(self, fig, markers_labels_text_dict = {}, point_annotation_bbox_args = dict(boxstyle="square", fc="0.9"), point_annotation_arrow_args = dict(arrowstyle="->")):
        self.fig = fig
        self.axes = fig.axes
        self.axes_siblings_dict = {ax : tuple(ax.get_shared_x_axes().get_siblings(ax)) for ax in self.axes} 
        self.current_ax = self.axes[0]
        self.current_ax_siblings_index = 0
        self.last_axes_siblings_index_dict = {}
        self.axes_siblings_annotation = {}
        self.hguides_dict = {}
        self.vguides_dict = {}
        self.markers_labels_text_dict = markers_labels_text_dict
        self.point_annotation_bbox_args = point_annotation_bbox_args
        self.point_annotation_arrow_args = point_annotation_arrow_args
        self.unique_axes_siblings = list(dict.fromkeys(self.axes_siblings_dict.values()))

        for ax_siblings in self.unique_axes_siblings:
            self.last_axes_siblings_index_dict[ax_siblings] = 0
            self.axes_siblings_annotation[ax_siblings] = ax_siblings[0].annotate(f"Ax : {self.current_ax_siblings_index}", xy = (0.28, 0.9), xycoords='axes fraction').draggable()
            self.hguides_dict[ax_siblings] = []
            self.vguides_dict[ax_siblings] = []

        self.current_ax_siblings = self.axes_siblings_dict[self.current_ax]

        self.toggle_crosshair = True
        self.snap_toggle = False

        self.xy_list = [] 

        self.hcrosshair_dict = {ax : [] for ax in self.axes}
        self.vcrosshair_dict = {ax : [] for ax in self.axes}
        self.crosshair_text_dict = {ax : None for ax in self.axes}
        self.last_point_index_dict = {ax : None for ax in self.axes}

        self.point_annotations_dict = {ax : {} for ax in self.axes}

        self.visible_axis_dict = {axes_siblings : [axes_siblings[0].xaxis] + [ax.yaxis for ax in axes_siblings] for axes_siblings in self.unique_axes_siblings}
        self.custom_ticklists_dict = {axes_siblings : {axis : [] for axis in self.visible_axis_dict[axes_siblings]} for axes_siblings in self.unique_axes_siblings}
        self.custom_ticklocators_dict = {axes_siblings : {} for axes_siblings in self.unique_axes_siblings}
        for axes_siblings in self.unique_axes_siblings:
            for axis in self.visible_axis_dict[axes_siblings]:
                axis_locator = cursor_locator(self, axis)
                self.custom_ticklocators_dict[axes_siblings][axis] = axis_locator
                axis.set_major_locator(axis_locator)

        for ax in self.axes:
            # Create crosshair lines and data display text for all axes
            self.hcrosshair_dict[ax] = ax.axhline(ax.get_ylim()[0], color="k", lw = 0.8, ls="--")
            self.vcrosshair_dict[ax] = ax.axvline(ax.get_xlim()[0], color="k", lw = 0.8, ls="--")
            self.crosshair_text_dict[ax] = ax.text(0.72, 0.9, '', transform=ax.transAxes)
            # Set all crosshair invisible until mouse event
            self.hcrosshair_dict[ax].set_visible(False)
            self.vcrosshair_dict[ax].set_visible(False)
            self.crosshair_text_dict[ax].set_visible(False)

    def update_xy_list(self):
        xy_list = []
        for line in self.current_ax.get_lines():
            if (line == self.hcrosshair_dict[self.current_ax]) or (line  == self.vcrosshair_dict[self.current_ax]) or (line in self.hguides_dict[self.current_ax_siblings]) or (line in self.vguides_dict[self.current_ax_siblings]):
                continue
            else:
                line_x_list, line_y_list = line.get_data()
                for i in range(len(line_x_list)):
                    x = line_x_list[i]
                    y = line_y_list[i]
                    xy_list.append([x, y])

        self.xy_list = xy_list

    def set_crosshair_visible(self, visible):
        need_redraw = self.hcrosshair_dict[self.current_ax].get_visible() != visible
        self.hcrosshair_dict[self.current_ax].set_visible(visible)
        self.vcrosshair_dict[self.current_ax].set_visible(visible)
        self.crosshair_text_dict[self.current_ax].set_visible(visible)
        return need_redraw

    def on_mouse_move(self, event):
        if not(event.inaxes in self.current_ax_siblings):
            need_redraw = self.set_crosshair_visible(False)
            if need_redraw:
                self.fig.canvas.draw()
        else:
            self.set_crosshair_visible(self.toggle_crosshair)
            xdata, ydata = self.current_ax.transData.inverted().transform((event.x, event.y))

            if self.snap_toggle and self.toggle_crosshair:

                if not(self.xy_list):
                    xlim = self.current_ax.get_xlim()
                    ylim = self.current_ax.get_ylim()
                    xdata, ydata = abs(xlim[1]-xlim[0])/2.0, abs(ylim[-1]-ylim[0])/2.0 
                else:

                    xy_list = [list(self.current_ax.transData.transform(point)) for point in self.xy_list]

                    index = xy_list.index(min(xy_list, key = lambda t : math.dist(t, [event.x, event.y])))

                    xdata, ydata = self.xy_list[index]

                    if (index == self.last_point_index_dict[self.current_ax]) :
                        return

                    self.last_point_index_dict[self.current_ax] = index

            self.hcrosshair_dict[self.current_ax].set_ydata([ydata])
            self.vcrosshair_dict[self.current_ax].set_xdata([xdata])
            self.crosshair_text_dict[self.current_ax].set_text(f"x={xdata:1.2g}, y={ydata:1.2g}")
            self.fig.canvas.draw()

    def on_mouse_click(self, event):
        if event.button == 1:
            if event.dblclick:
                if not (event.inaxes):
                    for ax in self.current_ax_siblings:
                        ax_xlim = ax.get_xlim()
                        ax_ylim = ax.get_ylim()
                        for i in range(len(ax.xaxis.get_ticklabels())):
                            if (ax.xaxis.get_ticklabels()[i].get_window_extent().contains(event.x, event.y)):
                                xticks_list = list(ax.xaxis.get_ticklocs())
                                xlabels_list = list(ax.xaxis.get_ticklabels())
                                if xticks_list[i] in self.custom_ticklists_dict[self.current_ax_siblings][self.current_ax_siblings[0].xaxis]:
                                    self.custom_ticklists_dict[self.current_ax_siblings][self.current_ax_siblings[0].xaxis].remove(xticks_list[i])
                                    self.fig.canvas.draw()
                                break
                        for i in range(len(ax.yaxis.get_ticklabels())):
                            if (ax.yaxis.get_ticklabels()[i].get_window_extent().contains(event.x, event.y)):
                                yticks_list = list(ax.yaxis.get_ticklocs())
                                ylabels_list = list(ax.yaxis.get_ticklabels())
                                if yticks_list[i] in  self.custom_ticklists_dict[self.current_ax_siblings][ax.yaxis]:
                                    self.custom_ticklists_dict[self.current_ax_siblings][ax.yaxis].remove(yticks_list[i])
                                    self.fig.canvas.draw()
                                break
                else:
                    target_ax = None
                    for ax in self.current_ax_siblings:
                        line_list = [line for line in ax.get_lines() if (not (line == self.hcrosshair_dict[ax]) and not(line == self.vcrosshair_dict[ax]))]
                        for line in line_list:
                            if line.contains(event)[0]:
                                target_x_ax = self.current_ax_siblings[-1]
                                target_y_ax = ax
                                target_x_ax_xlim = target_x_ax.get_xlim()
                                target_y_ax_ylim = target_y_ax.get_ylim()
                                
                    if target_ax == None:
                        target_x_ax = self.current_ax_siblings[-1] 
                        target_y_ax = self.current_ax
                        target_x_ax_xlim = target_x_ax.get_xlim()
                        target_y_ax_ylim = target_y_ax.get_ylim()

                    if self.snap_toggle and self.toggle_crosshair:
                        if not(self.xy_list):
                            xlim = target_x_ax_xlim
                            ylim = target_y_ax_ylim
                            xdata, ydata = abs(xlim[1]-xlim[0])/2.0, abs(ylim[-1]-ylim[0])/2.0 
                            target_point = [xdata, ydata]
                            xtick = target_point[0]
                            ytick = target_point[1]
                        else:
                            xy_list = [list(self.current_ax.transData.transform(point)) for point in self.xy_list]
                            index = xy_list.index(min(xy_list, key = lambda t : math.dist(t, [event.x, event.y])))
                            target_point = self.xy_list[index]
                            xtick = target_point[0]
                            ytick = target_point[1]
                    else:
                        xdata, ydata = target_x_ax.transData.inverted().transform((event.x, event.y))[0], target_y_ax.transData.inverted().transform((event.x, event.y))[1]
                        target_point = [xdata, ydata]
                        xtick = target_point[0]
                        ytick = target_point[1]

                    xtick = round(xtick, ndigits = 2)
                    ytick = round(ytick, ndigits = 2)
                    
                    if (xtick in self.custom_ticklists_dict[self.current_ax_siblings][self.current_ax_siblings[0].xaxis]) and (ytick in self.custom_ticklists_dict[self.current_ax_siblings][target_y_ax.yaxis]):
                        self.custom_ticklists_dict[self.current_ax_siblings][self.current_ax_siblings[0].xaxis].remove(xtick)
                        self.custom_ticklists_dict[self.current_ax_siblings][target_y_ax.yaxis].remove(ytick)
                    else:
                        if (xtick not in self.custom_ticklists_dict[self.current_ax_siblings][self.current_ax_siblings[0].xaxis]) and not(xtick in self.current_ax_siblings[0].xaxis.get_ticklocs()):
                            self.custom_ticklists_dict[self.current_ax_siblings][self.current_ax_siblings[0].xaxis].append(xtick)
                        if (ytick not in self.custom_ticklists_dict[self.current_ax_siblings][target_y_ax.yaxis]) and not(ytick in target_y_ax.yaxis.get_ticklocs()):
                            self.custom_ticklists_dict[self.current_ax_siblings][target_y_ax.yaxis].append(ytick)

                self.fig.canvas.draw()
        elif event.button == 3:
            if event.dblclick:
                self.toggle_crosshair = not(self.toggle_crosshair)
                self.set_crosshair_visible(self.toggle_crosshair)
                self.fig.canvas.draw()
            else:
                for ax in self.current_ax_siblings:
                    if self.point_annotations_dict[ax]:
                        annotation_dict = self.point_annotations_dict[ax]
                        for point in annotation_dict:
                            annotation = annotation_dict[point]
                            if self.snap_toggle and self.toggle_crosshair:
                                if (point[0] == self.vcrosshair_dict[self.current_ax].get_xdata()[0]) and (point[1] == self.hcrosshair_dict[self.current_ax].get_ydata()[0]):
                                    annotation.ref_artist.remove()
                                    del self.point_annotations_dict[self.current_ax][point]
                                    self.fig.canvas.draw()
                                    return
                                    
                            if annotation.ref_artist.get_window_extent().contains(event.x, event.y):
                                annotation.ref_artist.remove()
                                del self.point_annotations_dict[ax][point] 
                                self.fig.canvas.draw()
                                return

                    if self.snap_toggle and self.toggle_crosshair:

                        xdata, ydata = self.vcrosshair_dict[self.current_ax].get_xdata()[0], self.hcrosshair_dict[self.current_ax].get_ydata()[0]
                        transxdata, transydata = event.inaxes.transData.inverted().transform(self.current_ax.transData.transform((xdata, ydata)))
                        if not ((xdata,ydata) in self.point_annotations_dict[self.current_ax]):
                            if self.current_ax in self.markers_labels_text_dict:
                                annotation_text = f"{self.markers_labels_text_dict[self.current_ax][0]}: {xdata:1.2g}\n{self.markers_labels_text_dict[self.current_ax][1]}: {ydata:1.2g}"
                            else:
                                annotation_text = f"x{self.current_ax_siblings_index}: {xdata:1.2g}\ny{self.current_ax_siblings_index}: {ydata:1.2g}"
                            self.point_annotations_dict[self.current_ax][(xdata,ydata)] = event.inaxes.annotate(annotation_text, xy = (transxdata, transydata), bbox = self.point_annotation_bbox_args, arrowprops = self.point_annotation_arrow_args).draggable()
                        else:
                            self.point_annotations_dict[self.current_ax][(xdata,ydata)].ref_artist.remove()
                            del self.point_annotations_dict[self.current_ax][(xdata, ydata)]
                        self.fig.canvas.draw()
                        return
                    else:
                        for line in ax.get_lines():
                            if line.contains(event)[0] and (not (line == self.hcrosshair_dict[ax]) and not(line == self.vcrosshair_dict[ax])):
                                xlist, ylist = list(line.get_data()[0]), list(line.get_data()[1])
                                xdata, ydata = xlist[line.contains(event)[1]['ind'][0]], ylist[line.contains(event)[1]['ind'][0]]
                                if not (xdata,ydata) in self.point_annotations_dict[ax]:
                                    if ax in self.markers_labels_text_dict:
                                        annotation_text = f"{self.markers_labels_text_dict[ax][0]}: {xdata:1.2g}\n{self.markers_labels_text_dict[ax][1]}: {ydata:1.2g}"
                                    else:
                                        annotation_text = f"x{self.current_ax_siblings_index}: {xdata:1.2g}\ny{self.current_ax_siblings_index}: {ydata:1.2g}"
                                    (x, y) = ax.transData.transform((xdata, ydata))
                                    (new_xdata, new_ydata) = event.inaxes.transData.inverted().transform((x, y))
                                    self.point_annotations_dict[ax][(xdata,ydata)] = event.inaxes.annotate(annotation_text, xy = (new_xdata, new_ydata), bbox = self.point_annotation_bbox_args, arrowprops = self.point_annotation_arrow_args).draggable()
                                else:
                                    self.point_annotations_dict[ax][(xdata,ydata)].ref_artist.remove()
                                    del self.point_annotations_dict[ax][(xdata, ydata)]
                        self.fig.canvas.draw()

    def on_key_press(self, event):
        if event.key == "shift":
            self.snap_toggle = True
            
            if not(self.xy_list):
                xlim = self.current_ax.get_xlim()
                ylim = self.current_ax.get_ylim()
                xdata, ydata = abs(xlim[1]-xlim[0])/2.0, abs(ylim[1]-ylim[0])/2.0
            else:
                xdata, ydata = self.current_ax.transData.inverted().transform((event.x, event.y))

                xy_list = [list(self.current_ax.transData.transform(point)) for point in self.xy_list]

                index = xy_list.index(min(xy_list, key = lambda t : math.dist(t, [event.x, event.y])))

                xdata, ydata = self.xy_list[index]

                if (index == self.last_point_index_dict[self.current_ax]) :
                    return

                    self.last_point_index_dict[self.current_ax] = index

            self.hcrosshair_dict[self.current_ax].set_ydata([ydata])
            self.vcrosshair_dict[self.current_ax].set_xdata([xdata])
            self.crosshair_text_dict[self.current_ax].set_text(f"x={xdata:1.2g}, y={ydata:1.2g}")
            need_redraw = self.set_crosshair_visible(self.toggle_crosshair)
            self.fig.canvas.draw()
        if event.key == "enter" or event.key == "shift+enter":
            if not(event.inaxes):
                return
            create_guide = True
            if self.snap_toggle and self.toggle_crosshair:
                ydata = self.hcrosshair_dict[self.current_ax].get_ydata()[0]
                for guide in self.hguides_dict[self.current_ax_siblings]:
                    if guide.get_ydata()[0] == ydata:
                        guide.remove()
                        self.hguides_dict[self.current_ax_siblings].remove(guide)
                        create_guide = False
                        break
                if create_guide:
                    self.hguides_dict[self.current_ax_siblings].append(self.current_ax.axhline(ydata, color='k', lw=0.8))
            else:
                for guide in self.hguides_dict[self.current_ax_siblings]:
                        if guide.contains(event)[0]:
                            guide.remove()
                            self.hguides_dict[self.current_ax_siblings].remove(guide)
                            create_guide = False
                            break
                if create_guide:
                    ydata = self.current_ax_siblings[0].transData.inverted().transform((event.x, event.y))[1]
                    self.hguides_dict[self.current_ax_siblings].append(self.current_ax_siblings[0].axhline(ydata, color='k', lw=0.8))
            self.fig.canvas.draw()
        if event.key == "ctrl+enter" or event.key == "shift+ctrl+enter":
            if not(event.inaxes):
                return
            create_guide = True
            if self.snap_toggle and self.toggle_crosshair:
                xdata = self.vcrosshair_dict[self.current_ax].get_xdata()[0]
                for guide in self.vguides_dict[self.current_ax_siblings]:
                    if guide.get_xdata()[0] == xdata:
                        guide.remove()
                        self.vguides_dict[self.current_ax_siblings].remove(guide)
                        create_guide = False
                        break
                if create_guide:
                    self.vguides_dict[self.current_ax_siblings].append(self.current_ax.axvline(xdata, color='k', lw=0.8))
            else:
                for guide in self.vguides_dict[self.current_ax_siblings]:
                        if guide.contains(event)[0]:
                            guide.remove()
                            self.vguides_dict[self.current_ax_siblings].remove(guide)
                            create_guide = False
                            break
                if create_guide:
                    xdata = event.xdata
                    self.vguides_dict[self.current_ax_siblings].append(self.current_ax_siblings[0].axvline(xdata, color='k', lw=0.8))
            self.fig.canvas.draw()
        if event.key == "backspace":
            for i in range(len(self.hguides_dict[self.current_ax_siblings])):
                self.hguides_dict[self.current_ax_siblings][0].remove()
                del self.hguides_list[self.current_ax_siblings][0]
            for i in range(len(self.vguides_dict[self.current_ax_siblings])):
                self.vguides_dict[self.current_ax_siblings][0].remove()
                del self.vguides_dict[self.current_ax_siblings][0]
            self.fig.canvas.draw()
        if event.key == "right": 
            self.set_crosshair_visible(False)
            new_ax_index = (self.current_ax_siblings_index+1) % len(self.current_ax_siblings)
            self.current_ax = self.current_ax_siblings[-1-new_ax_index]
            self.current_ax_siblings_index = new_ax_index
            self.last_axes_siblings_index_dict[self.current_ax_siblings] = new_ax_index
            self.current_ax_siblings_index = new_ax_index 
            self.update_xy_list()
            need_draw = self.set_crosshair_visible(self.toggle_crosshair)
            self.axes_siblings_annotation[self.current_ax_siblings].ref_artist.set_text(f"Ax : {self.current_ax_siblings_index}")
            self.fig.canvas.draw()
            self.on_mouse_move(event)
        if event.key == "left": 
            self.set_crosshair_visible(False)
            new_ax_index = (self.current_ax_siblings_index-1) % len(self.current_ax_siblings)
            self.current_ax = self.current_ax_siblings[-1-new_ax_index]
            self.current_ax_siblings_index = new_ax_index
            self.last_axes_siblings_index_dict[self.current_ax_siblings] = new_ax_index
            self.current_ax_siblings_index = new_ax_index 
            self.update_xy_list()
            need_draw = self.set_crosshair_visible(self.toggle_crosshair)
            self.axes_siblings_annotation[self.current_ax_siblings].ref_artist.set_text(f"Ax : {self.current_ax_siblings_index}")
            self.fig.canvas.draw()
            self.on_mouse_move(event)

    def on_key_release(self, event):
        if event.key == "shift" or event.key == "shift+ctrl":
            self.snap_toggle = False
            xdata, ydata = self.current_ax.transData.inverted().transform((event.x, event.y))
            self.hcrosshair_dict[self.current_ax].set_ydata([ydata])
            self.vcrosshair_dict[self.current_ax].set_xdata([xdata])
            self.crosshair_text_dict[self.current_ax].set_text(f"x={xdata:1.2g}, y={ydata:1.2g}")
            self.fig.canvas.draw()


    def on_enter_axes(self, event):
        self.current_ax_siblings = self.axes_siblings_dict[event.inaxes]
        self.current_ax = self.current_ax_siblings[-1-self.last_axes_siblings_index_dict[self.current_ax_siblings]]
        self.current_ax_siblings_index = self.last_axes_siblings_index_dict[self.current_ax_siblings]
        self.update_xy_list()
        self.on_mouse_move(event)


    def on_exit_axes(self, event):
        self.xy_list = []        

class cursor_locator(ticker.AutoLocator):
    def __init__(self, cursor, axis):
        super().__init__()
        self.set_axis(axis)
        self.cursor = cursor
        self.custom_ticklist = cursor.custom_ticklists_dict[cursor.axes_siblings_dict[self.axis.axes]][self.axis]
    def tick_values(self, vmin, vmax):
        if self._symmetric:
            vmax = max(abs(vmin), abs(vmax))
            vmin = -vmax
        vmin, vmax = nonsingular(
            vmin, vmax, expander=1e-13, tiny=1e-14)
        locs = self._raw_ticks(vmin, vmax)

        prune = self._prune
        if prune == 'lower':
            locs = locs[1:]
        elif prune == 'upper':
            locs = locs[:-1]
        elif prune == 'both':
            locs = locs[1:-1]
        return self.raise_if_exceeds(locs)
    def __call__(self):
        vmin, vmax = self.axis.get_view_interval()
        ticklocs = list(self.tick_values(vmin, vmax))
        for custom_tick in self.cursor.custom_ticklists_dict[self.cursor.axes_siblings_dict[self.axis.axes]][self.axis]:
            for i in range(len(ticklocs)-1):
                if (custom_tick >= ticklocs[i]) and (custom_tick < ticklocs[i+1]) :
                    ticklocs.insert(i+1, custom_tick)
                    break
        ticklocs = np.array(ticklocs)
            

        return ticklocs 

if __name__ == "__main__":

    N_list = list(range(1, 30))
    s_list = list(range(1, 30))
    s_2_list = [elt/30 for elt in list(range(30, 1, -1))]

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()


    ax1.plot(N_list, s_list, 'g-', marker = 'o')
    ax2.plot(N_list, s_2_list, 'b-', marker = 'o')

    Cursor = custom_cursor(fig, markers_labels_text_dict = {ax1: ("N", "s"), ax2: ("N", "s2")})


    fig.canvas.mpl_connect('button_press_event', Cursor.on_mouse_click)
    fig.canvas.mpl_connect('motion_notify_event', Cursor.on_mouse_move)
    fig.canvas.mpl_connect('axes_enter_event', Cursor.on_enter_axes)
    fig.canvas.mpl_connect('axes_leave_event', Cursor.on_exit_axes)
    fig.canvas.mpl_connect('key_press_event', Cursor.on_key_press)
    fig.canvas.mpl_connect('key_release_event', Cursor.on_key_release)

    plt.show()
