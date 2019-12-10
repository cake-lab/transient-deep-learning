def heatmap(data, row_labels, col_labels, ax=None,
            cbar_kw={}, cbarlabel="", **kwargs):
    """
    Create a heatmap from a numpy array and two lists of labels.

    Arguments:
        data       : A 2D numpy array of shape (N,M)
        row_labels : A list or array of length N with the labels
                     for the rows
        col_labels : A list or array of length M with the labels
                     for the columns
    Optional arguments:
        ax         : A matplotlib.axes.Axes instance to which the heatmap
                     is plotted. If not provided, use current axes or
                     create a new one.
        cbar_kw    : A dictionary with arguments to
                     :meth:`matplotlib.Figure.colorbar`.
        cbarlabel  : The label for the colorbar
    All other arguments are directly passed on to the imshow call.
    """

    if not ax:
        ax = plt.gca()

    # Plot the heatmap
    im = ax.imshow(data, **kwargs)

    # Create colorbar
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="4%", pad=0.05)
    cbar = ax.figure.colorbar(im, cax=cax, **cbar_kw)
    cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom")
    cbar.set_ticks([1.0,0.9,0.8,0.7,0.6,0.5,0.4,0.3,0.2])

    # We want to show all ticks...
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_yticks(np.arange(data.shape[0]))
    # ... and label them with the respective list entries.
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)

    # Let the horizontal axes labeling appear on top.
    ax.tick_params(top=True, bottom=False,
                   labeltop=True, labelbottom=False)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=-30, ha="right",
             rotation_mode="anchor")

    # Turn spines off and create white grid.
    for edge, spine in ax.spines.items():
        spine.set_visible(False)

    ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
    ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
    ax.tick_params(which="minor", bottom=False, left=False)

    return im, cbar

def annotate_heatmap(im, data=None, valfmt="{x:.2f}",
                     textcolors=["black", "white"],
                     threshold=None, **textkw):
    """
    A function to annotate a heatmap.

    Arguments:
        im         : The AxesImage to be labeled.
    Optional arguments:
        data       : Data used to annotate. If None, the image's data is used.
        valfmt     : The format of the annotations inside the heatmap.
                     This should either use the string format method, e.g.
                     "$ {x:.2f}", or be a :class:`matplotlib.ticker.Formatter`.
        textcolors : A list or array of two color specifications. The first is
                     used for values below a threshold, the second for those
                     above.
        threshold  : Value in data units according to which the colors from
                     textcolors are applied. If None (the default) uses the
                     middle of the colormap as separation.

    Further arguments are passed on to the created text labels.
    """

    if not isinstance(data, (list, np.ndarray)):
        data = im.get_array()

    # Normalize the threshold to the images color range.
    if threshold is not None:
        threshold = im.norm(threshold)
    else:
        threshold = im.norm(data.max())/2.

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center",
              verticalalignment="center")
    kw.update(textkw)

    # Get the formatter in case a string is supplied
    if isinstance(valfmt, str):
        valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

    # Loop over the data and create a `Text` for each "pixel".
    # Change the text's color depending on the data.
    texts = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            kw.update(color=textcolors[im.norm(data[i, j]) > threshold])
            text = im.axes.text(j, i, valfmt(data[i, j], None), **kw)
            texts.append(text)

    return texts

with open('/Users/ozymandias/Desktop/spotTrain_data/8-spot/vm_data.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    next(csv_reader, None)
    vm_data = []
    ventry = {}
    ventry['name'] = None
    ventry['time'] = None
    ventry['accuracy'] = None
    ventry['revoke'] = None
    for vm in csv_reader:
        ventry = {}
        ventry['name'] = vm[0]
        ventry['time'] = vm[1]
        ventry['revoke'] = vm[2]
        ventry['reltime'] = None
        run = vm[0].split('-')[0] + '-' +vm[0].split('-')[1]+'-'+vm[0].split('-')[2]+'-'+vm[0].split('-')[3]
        vm_data.append(ventry)
        ventry = {}
        ventry['name'] = None
        ventry['time'] = None
        ventry['reltime'] = None
        ventry['revoke'] = None

with open('/Users/ozymandias/Desktop/spotTrain_data/8-spot/train_data_processed.csv') as file:
    csv_reader = csv.reader(file, delimiter=',')
    next(csv_reader, None)
    train_data = []
    entry = {}
    entry['run'] = None
    entry['time'] = None
    entry['accuracy'] = None
    entry['num_rev'] = 0
    for cluster in csv_reader:
        entry['run'] = cluster[0] + '-run' + cluster[1]
        entry['time'] = cluster[2]
        entry['accuracy'] = cluster[3]
        entry['num_rev'] = 0
        train_data.append(entry)
        entry = {}
        entry['run'] = None
        entry['time'] = None
        entry['accuracy'] = None

count = 0
for i in range(len(vm_data)):
    if count % 8 == 0:
        length = vm_data[i]['time']
    if vm_data[i]['revoke'] != 'Job completed' and vm_data[i]['revoke'] != 'Job Completed' and vm_data[i]['revoke'] != 'Manually stopped due to revoked master':
        train_data[i // 8]['num_rev'] += 1
        vm_data[i]['reltime'] = float(vm_data[i]['time']) / float(length)
    else:
        vm_data[i]['reltime'] = 1
    count += 1

val = []
subval = []

count = 0
for i in vm_data:
    count += 1
    subval.append(i['reltime'])
    if count % 8 == 0:
        subval.sort()
        val.append(subval)
        subval = []

def helper(ele):
    return ele[0]['num_rev']
        
list1, list2 = (list(t) for t in zip(*sorted(zip(train_data, val), key=helper, reverse=True)))
fig = plt.figure()
fig.tight_layout()
figure(num=None, figsize=(20, 10), dpi=100, facecolor='w', edgecolor='k')
im, cbar = heatmap(np.transpose(list2),[],[], cmap='gray_r')
plt.yticks(np.arange(8), [])
plt.show()