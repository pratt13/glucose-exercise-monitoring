# from numpy import convolve


class Data:
    """
    Basic class to process some data

    TODO: To split up/abstract further down the line

    """

    @staticmethod
    def plot_figure(data):
        import matplotlib.pyplot as plt

        fig = plt.figure()
        fig.savefig("temp.png")

    def create_graph(self, data):
        data = [(4.2, "2024-07-23 08:43:35"), (3.6, "2024-07-23 08:58:35")]
        print(self._moving_average(data))

    @staticmethod
    def _moving_time_average(data):
        """
        Take a list of data records (values,timestamp), and compute the average between them,
        creating a smoother average. This has the impact of smoothing out peaks if the interval
        is too wide.
        """
        pass

    def _savgol_filter(self, data, n=3):
        """
        Smooth the data via the savgol_filter
        """
        pass
