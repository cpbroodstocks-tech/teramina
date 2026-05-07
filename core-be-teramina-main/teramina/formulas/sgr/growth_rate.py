"""this is Specific Growth Rate (SGR)"""

class Sgr:
    """specific growth rate"""

    def __init__(self, data: list) -> None:
        """initialization

        Args:
            data (list): list of abw
        """
        self.data = data

    def sgr_function(self, abw: float, init_abw: float, shifted: int):
        """sgr function

        Args:
            abw (float): average body weight
            init_abw (float): initiate abw
            shifted (int): shifted of sampling doc
        """
        if init_abw is None or abw is None:
            return None
        if init_abw == abw:
            return None
        return (abw - init_abw)/shifted

    def calculate(self):
        """calculate the sgr"""
        sgr_pool = []
        init_abw = None
        init_t = 0
        for t, abw in enumerate(self.data):
            sgr_pool.append(self.sgr_function(abw, init_abw, t-init_t))
            if abw:
                init_abw = abw
                init_t = t
        return sgr_pool
