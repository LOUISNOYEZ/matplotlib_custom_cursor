import math
import matplotlib.pyplot as plt

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

        for ax_siblings in list(dict.fromkeys(self.axes_siblings_dict.values())):
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

            if self.snap_toggle:

                if not(self.xy_list):
                    xlim = self.current_ax.get_xlim()
                    ylim = self.current_ax.get_ylim()
                    xdata, ydata = abs(xlim[1]-xlim[0])/2.0, abs(ylim[-1]-ylim[0])/2.0 
                else:

                    index = self.xy_list.index(min(self.xy_list, key = lambda t : math.dist(t, [xdata, ydata])))

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
                    for ax in self.axes:
                        ax_xlim = ax.get_xlim()
                        ax_ylim = ax.get_ylim()
                        for i in range(len(ax.xaxis.get_ticklabels())):
                            if (ax.xaxis.get_ticklabels()[i].get_window_extent().contains(event.x, event.y)):
                                xticks_list = list(ax.xaxis.get_ticklocs())
                                xlabels_list = list(ax.xaxis.get_ticklabels())
                                del xticks_list[i]
                                del xlabels_list[i]
                                ax.set_xticks(xticks_list, labels = xlabels_list)
                                ax.set_xlim(ax_xlim)
                                ax.set_ylim(ax_ylim)
                                self.fig.canvas.draw()
                                break
                        for i in range(len(ax.yaxis.get_ticklabels())):
                            if (ax.yaxis.get_ticklabels()[i].get_window_extent().contains(event.x, event.y)):
                                yticks_list = list(ax.yaxis.get_ticklocs())
                                ylabels_list = list(ax.yaxis.get_ticklabels())
                                del yticks_list[i]
                                del ylabels_list[i]
                                ax.set_yticks(yticks_list, labels = ylabels_list)
                                ax.set_xlim(ax_xlim)
                                ax.set_ylim(ax_ylim)
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

                    xticks_list = list(target_x_ax.xaxis.get_ticklocs())
                    xlabels_list = list(target_x_ax.xaxis.get_ticklabels())
                    yticks_list = list(target_y_ax.yaxis.get_ticklocs())
                    ylabels_list = list(target_y_ax.yaxis.get_ticklabels())
                    
                    if self.snap_toggle:
                        if not(self.xy_list):
                            xlim = target_x_ax_xlim
                            ylim = target_y_ax_ylim
                            xdata, ydata = abs(xlim[1]-xlim[0])/2.0, abs(ylim[-1]-ylim[0])/2.0 
                            target_point = [xdata, ydata]
                            xtick = target_point[0]
                            ytick = target_point[1]
                            xlabel = f"{xtick:1.2f}"
                            ylabel = f"{ytick:1.2f}"
                        else:
                            xdata, ydata = target_x_ax.transData.inverted().transform((event.x, event.y))[0], target_y_ax.transData.inverted().transform((event.x, event.y))[1]
                            target_point = min(self.xy_list, key = lambda t : math.dist(t, [xdata, ydata]))
                            xtick = target_point[0]
                            ytick = target_point[1]
                            xlabel = f"{xtick}"
                            ylabel = f"{ytick}"
                    else:
                        xdata, ydata = target_x_ax.transData.inverted().transform((event.x, event.y))[0], target_y_ax.transData.inverted().transform((event.x, event.y))[1]
                        target_point = [xdata, ydata]
                        xtick = target_point[0]
                        ytick = target_point[1]
                        xlabel = f"{xtick:1.2f}"
                        ylabel = f"{ytick:1.2f}"
                    
                    if (xtick in xticks_list) and (ytick in yticks_list):
                        xticks_list.remove(xtick)
                        xlabels_list = [elt for elt in xlabels_list if not elt.get_text() == xlabel]
                        yticks_list.remove(ytick)
                        ylabels_list = [elt for elt in ylabels_list if not elt.get_text() == ylabel]
                        target_x_ax.set_xticks(xticks_list, labels = xlabels_list)
                        target_y_ax.set_yticks(yticks_list, labels = ylabels_list)
                    else:
                        if (xtick not in xticks_list):
                            xticks_list.append(xtick)
                            xlabels_list.append(xlabel)
                            target_x_ax.set_xticks(xticks_list, labels = xlabels_list)
                        if (ytick not in yticks_list):
                            yticks_list.append(ytick)
                            ylabels_list.append(ylabel)
                            target_y_ax.set_yticks(yticks_list, labels = ylabels_list)

                    target_x_ax.set_xlim(target_x_ax_xlim)
                    target_y_ax.set_ylim(target_y_ax_ylim)

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
                        transxdata, transydata = self.current_ax_siblings[0].transData.inverted().transform(self.current_ax.transData.transform((xdata, ydata)))
                        if not ((xdata,ydata) in self.point_annotations_dict[self.current_ax]):
                            if self.current_ax in self.markers_labels_text_dict:
                                annotation_text = f"{self.markers_labels_text_dict[self.current_ax][0]}: {xdata:1.2g}\n{self.markers_labels_text_dict[self.current_ax][1]}: {ydata:1.2g}"
                            else:
                                annotation_text = f"x{self.current_ax_siblings_index}: {xdata:1.2g}\ny{self.current_ax_siblings_index}: {ydata:1.2g}"
                            self.point_annotations_dict[self.current_ax][(xdata,ydata)] = self.current_ax_siblings[0].annotate(annotation_text, xy = (transxdata, transydata), bbox = self.point_annotation_bbox_args, arrowprops = self.point_annotation_arrow_args).draggable()
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
                                    self.point_annotations_dict[ax][(xdata,ydata)] = ax.annotate(annotation_text, xy = (xdata, ydata), bbox = self.point_annotation_bbox_args, arrowprops = self.point_annotation_arrow_args).draggable()
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

                index = self.xy_list.index(min(self.xy_list, key = lambda t : math.dist(t, [xdata, ydata])))

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
                    ydata = event.ydata
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
            self.hcrosshair_dict[self.current_ax].set_ydata(ydata)
            self.vcrosshair_dict[self.current_ax].set_xdata(xdata)
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

if __name__ == "__main__":

    N_list = list(range(1, 30))
    s_list = list(range(1, 30))
    s_2_list = [elt/30 for elt in list(range(30, 1, -1))]

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    Cursor = custom_cursor(fig, markers_labels_text_dict = {ax1: ("N", "s"), ax2: ("N", "s2")})

    ax1.plot(N_list, s_list, 'g-', marker = 'o')
    ax2.plot(N_list, s_2_list, 'b-', marker = 'o')

    fig.canvas.mpl_connect('button_press_event', Cursor.on_mouse_click)
    fig.canvas.mpl_connect('motion_notify_event', Cursor.on_mouse_move)
    fig.canvas.mpl_connect('axes_enter_event', Cursor.on_enter_axes)
    fig.canvas.mpl_connect('axes_leave_event', Cursor.on_exit_axes)
    fig.canvas.mpl_connect('key_press_event', Cursor.on_key_press)
    fig.canvas.mpl_connect('key_release_event', Cursor.on_key_release)

    plt.show()
