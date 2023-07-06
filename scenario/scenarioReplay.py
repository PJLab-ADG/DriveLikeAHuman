import sqlite3
from matplotlib import pyplot as plt
from matplotlib import patches as mpatch
import base64
from io import BytesIO


class ScenarioReplay:
    def __init__(self, database: str) -> None:
        self.database = database

    def getVehicles(self, frame: int):
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()
        cur.execute(
            f"""SELECT id, x, y FROM vehINFO WHERE frame={frame};"""
        )
        frameVehINFO = cur.fetchall()
        conn.close()
        return frameVehINFO

    def plotSce(self, frame: int) -> str:
        vehiclesINFO = self.getVehicles(frame)
        vehiclesINFO.sort(key=lambda veh: veh[1])
        minx = vehiclesINFO[0][1] - 20
        maxx = vehiclesINFO[-1][1] + 20
        plt.figure(figsize=(22, 6))
        plt.axis('equal')
        for veh in vehiclesINFO:
            leftBottom = (veh[1]-2.5, veh[2]-1)
            if veh[0] == 'ego':
                rect = mpatch.Rectangle(leftBottom, 5.0, 2.0, color='#fd9644')

            else:
                rect = mpatch.Rectangle(leftBottom, 5.0, 2.0, color='#0fb9b1')
            plt.annotate(veh[0], (veh[1]-2.5, veh[2]+1.5),
                         fontsize=14, color='#fc5c65')
            plt.gca().add_patch(rect)
        plt.plot([minx, maxx], [-2, -2], color='#778ca3')
        plt.plot([minx, maxx], [2, 2], linestyle='dashed', color='#d1d8e0')
        plt.plot([minx, maxx], [6, 6], linestyle='dashed',  color='#d1d8e0')
        plt.plot([minx, maxx], [10, 10], linestyle='dashed', color='#d1d8e0')
        plt.plot([minx, maxx], [14, 14], color='#778ca3')
        # reverse the y-axis
        plt.gca().invert_yaxis()
        buffer = BytesIO()
        plt.savefig(buffer, bbox_inches='tight')
        plt.close()
        plot_data = buffer.getvalue()
        imb = base64.b64encode(plot_data)
        ims = imb.decode()
        imd = 'data:image/png;base64,' + ims
        return imd
