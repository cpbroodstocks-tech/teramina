# pylint: disable=R0801
""""simple weight function based on adg"""


def wt(t0, t, w0: float = 0.05, initial_adg: float = 0.15):
    """basic weight function based on adg

        adg = w(t) - w(t-1)
        w(t+i) = w(t) + i * adg

        in this case we set the i=1
    Args:
        t (int): max doc
        t0 (int): start doc. default t0=1
        w0 (float): initial weight. default w0=0.05
        initial_adg (float): initial_adg value
    """
    wt_list = []

    doc = list(range(t0, t))
    for i, _ in enumerate(doc):
        if i == 0:
            wt_list.append(w0)
        elif i == 1:
            wt_list.append(wt_list[-1] + initial_adg)
        else:
            wt_list.append(2 * wt_list[-1] - wt_list[-2])
    return wt_list
