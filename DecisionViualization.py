"""
- 本代码用以展示 LLMDriver 在每个决策点看到的场景，以及其做出决策的过程。
- This code is used to display the scene seen by the LLMDriver at each decision point, as well as the process of making decisions.
"""

import base64
from flask import Flask, jsonify, render_template, request
import sqlite3

from scenario.scenarioReplay import ScenarioReplay

# 修改为对应的数据库名称
databaseName = './results-db/highwayv0.db'
sr = ScenarioReplay(databaseName)
app = Flask(__name__)


@app.route("/")
def mainWindow():
    conn = sqlite3.connect(databaseName)
    cur = conn.cursor()
    cur.execute(
        """SELECT min(frame), max(frame) FROM decisionINFO;"""
    )
    minFrame, maxFrame = cur.fetchone()
    conn.close()
    return render_template(
        'start.html', minFrame=minFrame, maxFrame=maxFrame
        )

@app.route("/get_frame", methods=['POST'])
def getFrame():
    frame = int(request.form['frame'])
    imd = sr.plotSce(frame)
    conn = sqlite3.connect(databaseName)
    cur = conn.cursor()
    cur.execute(
        f"""SELECT scenario, thoughtsAndActions, finalAnswer, outputParser FROM decisionINFO WHERE frame = {frame};"""
    )
    scenario, thoughtsAndActions, finalDecision, outputParser = cur.fetchone()
    outputParser = base64.b64decode(outputParser).decode('utf-8')
    conn.close()
    return jsonify(
        img=imd, scenario=scenario, 
        thoughtsAndActions=thoughtsAndActions, 
        finalDecision=finalDecision,
        outputParser =outputParser)


if __name__ == '__main__':
    app.run()
