import json
import pandas as pd

'''
adofai lib by TonyLimps 2025
bug fix & dlc support by Skyland_Redstone 2025
'''


class adofai:
    # adofai 2.9.2发卡弯带暂停bug状态:
    # 双球: 0
    # 三球: 1
    # bug更新后只需要修改下方两个常量
    TWO_PLANET_PAUSE_BEAT_DIFF = 0
    THREE_PLANET_PAUSE_BEAT_DIFF = 1

    def __init__(self, path):

        # adofai(adofai文件路径) 这是一个adofai类

        with open(path, 'r', encoding='utf-8-sig') as text:
            # 读取文件并转为字典
            text = text.read()
            text = text.replace('""', '"\\\\0"').replace(',}', '').replace('\n', '')
            Dict = json.loads(text)
            try:
                self.pathData = Dict['pathData']
            except KeyError:
                self.angleData = Dict['angleData']
            self.settings = Dict['settings']
            self.actions = Dict['actions']
            try:
                self.decorations = Dict['decorations']
            except KeyError:
                self.decorations = []

    def getRotateAngle(self):
        # adofai().getRotateAngle()
        # 将angledata转为球在每个轨道上旋转的角度,返回一个列表

        angleData = self.__dict__['angleData']
        planetNumList = self.getPlanetNumList()
        holdList = self.getHoldList()

        # 限制角度取值范围(0,360]
        for i in range(len(angleData)):
            if angleData[i] <= 0:
                angleData[i] += 360

        # 计算球的旋转角度
        # 下面将中旋底下的不用点击的轨道称作中旋轨道
        rotateAngleList = [0]
        for i in range(1, len(angleData)):
            try:
                if angleData[i - 1] == 999:
                    # 如果上一个轨道是中旋轨道就跳过,无需计算
                    continue
                if angleData[i] == 999:
                    # 当这个轨道是中旋轨道时
                    # 将上个轨道和下个轨道的角度记录
                    absoluteAngle1 = angleData[i - 1]
                    absoluteAngle2 = angleData[i + 1]
                if angleData[i] != 999:
                    # 如果这个轨道不是中旋轨道
                    # 将上个轨道的角度加180,记录轨道角度
                    absoluteAngle1 = angleData[i - 1] + 180
                    absoluteAngle2 = angleData[i]
            except IndexError:
                # 报List index out of range了说明
                # 最后一个轨道是中旋轨道,没有[i+1]这一项
                # 用普通方法计算
                absoluteAngle1 = angleData[i - 1] + 180

            if absoluteAngle1 > 360:
                # 限制轨道角度的取值(0,360]
                absoluteAngle1 -= 360

            # 计算球的旋转角度
            rotateAngle = absoluteAngle1 - absoluteAngle2

            if rotateAngle <= 0:
                # 限制角度的取值在0~360
                rotateAngle += 360

            # 将角度添加到返回值列表
            rotateAngleList.append(rotateAngle)

        # 返回值列表中没有中旋轨道
        # 需要还原中旋轨道的位置,避免下面处理事件时层数对不上
        for i in range(len(angleData)):
            if angleData[i] == 999:
                rotateAngleList.insert(i, 999)

        # 处理旋转事件
        # 把所有旋转事件的轨道层数记录为列表_twirlFloorList
        # 并转化成[[a,b],[c,d],[e,f]]的形式
        actions = self.__dict__['actions']
        _twirlFloorList = []
        for i in actions:
            if i['eventType'] == 'Twirl':
                _twirlFloorList.append(i['floor'])
        twirlFloorList = []
        for i in range(0, len(_twirlFloorList), 2):
            twirlFloorList.append(_twirlFloorList[i: i + 2])

        # 用for循环遍历其中的每个小列表,就能实现:
        # 只处理奇数次旋转,偶数次不处理
        # 这么做比一个个处理旋转事件快得多

        hairpinTurnDiff = {}  # 记录发卡弯,适配发卡弯暂停会多/少一拍的bug
        for i in twirlFloorList:
            if len(i) == 2:
                # 如果列表里有2个元素(一般情况)
                for j in range(i[0], i[1]):
                    # 从列表中的第一个数遍历到第二个数
                    if rotateAngleList[j] < 360:
                        # 为什么旋转角度<360才会处理事件？
                        # 之前的代码中我已经把角度取值限制在了(0,360]
                        # 如果角度等于360,就算旋转了在游戏中仍然要转360度
                        # 如果这个轨道是中旋轨道,那么角度是999,也能排除在外
                        # 避免影响后面去除中选轨道
                        rotateAngleList[j] = 360 - rotateAngleList[j]  # 旋转后的角度为360-原角度
                    elif rotateAngleList[j] == 360:
                        hairpinTurnDiff[j] = self.TWO_PLANET_PAUSE_BEAT_DIFF
            if len(i) == 1:
                # 如果列表只有1个元素
                # (说明一共有奇数个旋转,而且这是最后一个旋转)
                for j in range(i[0], len(rotateAngleList)):
                    # 从列表中的第一个数遍历到旋转角度列表的尾部
                    if rotateAngleList[j] < 360:
                        rotateAngleList[j] = 360 - rotateAngleList[j]

        # 处理三球事件
        lastTileOfThreePlanets = -1
        planetNumList[len(rotateAngleList)] = 2  # 最后清算持续到结束的三球
        for i in planetNumList:
            if planetNumList[i] == 3 and lastTileOfThreePlanets == -1:
                lastTileOfThreePlanets = i
            elif planetNumList[i] == 2 and lastTileOfThreePlanets != -1:
                for j in range(lastTileOfThreePlanets, i):
                    if rotateAngleList[j] == 360:
                        hairpinTurnDiff[j] = self.THREE_PLANET_PAUSE_BEAT_DIFF
                    rotateAngleList[j] -= 60
                    if rotateAngleList[j] <= 0:
                        rotateAngleList[j] += 360
                lastTileOfThreePlanets = -1

        # 处理长按事件
        # 注意忽略最后一格的长按
        for i in holdList:
            if i < len(rotateAngleList):
                rotateAngleList[i] += holdList[i]

        # 处理暂停节拍事件
        # 找到暂停节拍事件后在对应层数的轨道的角度上加上 拍子数*180
        hairpinTurnTiles = list(hairpinTurnDiff.keys())
        index = 0
        cntHairpin = len(hairpinTurnTiles)
        for i in actions:
            if i['eventType'] == 'Pause':
                while index < cntHairpin and hairpinTurnTiles[index] < i['floor']:
                    index += 1
                if rotateAngleList[i['floor']] == 360:
                    # 适配发卡弯bug
                    # 三球多一拍,二球少一拍
                    rotateAngleList[i['floor']] += max(i['duration'] + hairpinTurnDiff[hairpinTurnTiles[index]],
                                                       0) * 180
                else:
                    # 正常情况
                    rotateAngleList[i['floor']] += i['duration'] * 180

        # 去掉返回值里的中旋轨道
        for i in rotateAngleList:
            if i == 999:
                rotateAngleList.pop(rotateAngleList.index(999))

        self.rotateAngleList = rotateAngleList
        return rotateAngleList

    def getBeatList(self):
        # adofai().getBeatList()
        # 返回轨道代表的拍子数(列表,与bpm无关,是轨道角度/180)
        rotateAngle = self.getRotateAngle()
        beatList = []
        for i in range(len(rotateAngle)):
            beatList.append(rotateAngle[i] / 180)
        self.beatList = beatList
        return beatList

    def getPlanetNumList(self):
        # adofai().getPlanetNumList()
        # 返回行星个数的变化情况(字典,格式为{轨道层数:行星个数,轨道层数:行星个数})
        actions = self.__dict__['actions']
        planetNumList = {0: 2}
        for i in actions:
            if i['eventType'] == 'MultiPlanet':
                if i['planets'] == 'ThreePlanets':
                    planetNumList[i['floor']] = 3
                else:
                    planetNumList[i['floor']] = 2
        self.planetNumList = planetNumList
        return planetNumList

    def getBpmList(self):
        # adofai().getBpmList()
        # 返回bpm变化情况(字典,格式为{轨道层数:bpm,轨道层数:bpm})
        bpm = self.__dict__['settings']['bpm']
        actions = self.__dict__['actions']
        bpmList = {0: bpm}
        for i in actions:
            if i['eventType'] == 'SetSpeed':
                if i['speedType'] == 'Bpm':
                    bpmList[i['floor']] = i['beatsPerMinute']
                    bpm = i['beatsPerMinute']
                if i['speedType'] == 'Multiplier':
                    bpm *= i['bpmMultiplier']
                    bpmList[i['floor']] = bpm
        self.bpmList = bpmList
        return bpmList

    def getAbsBeatList(self, bpm=-1):
        # adofai().getAbsBeatList(bpm)
        # 返回绝对节拍(列表,代表每个轨道在规定bpm下代表多少拍)
        # bpm不填时默认为谱面原bpm

        # 初始化
        try:
            angleData = self.__dict__['angleData']
        except KeyError:
            self.pathDataToAngleData()
            angleData = self.__dict__['angleData']
        if bpm < 0:
            # 默认bpm
            bpm = self.settings['bpm']

        # 还原中旋轨道
        midspinList = []
        for i in range(len(angleData)):
            if angleData[i] == 999:
                midspinList.append(i)
        beats = self.getBeatList()
        bpmList = self.getBpmList()
        keys = list(bpmList.keys())
        for i in midspinList:
            beats.insert(i, 999)

        # 处理速度事件
        # 将与bpm无关的节拍根据bpmList中的速度变化情况
        # 变为在指定bpm下轨道代表的拍子数

        for i in range(len(keys)):
            retbpm = bpmList[keys[i]]
            muliter = retbpm / bpm
            _from = keys[i]
            try:
                _to = keys[i + 1]
            except IndexError:
                _to = len(beats)

            for j in range(_from, _to):
                if beats[j] != 999:
                    beats[j] /= muliter
        absoluteBeatList = []
        for i in beats:
            if i != 999:
                absoluteBeatList.append(i)

        self.absBeatList = absoluteBeatList
        return absoluteBeatList

    def getHoldList(self):
        # adofai().getHoldList()
        # 返回长按事件的出现情况(字典,格式为{轨道层数:额外长按度数,轨道层数:额外长按度数})
        actions = self.__dict__['actions']
        holdList = {}
        for i in actions:
            if i['eventType'] == 'Hold':
                holdList[i['floor']] = i['duration'] * 360
        self.holdList = holdList
        return holdList

    def angleDataToPathData(self):
        # adofai().angleDataToPathData()
        # 无返回值,把adofai()里的angleData转化成pathData
        mapping = {
            0: 'R',
            15: 'p',
            30: 'j',
            45: 'E',
            60: 'T',
            75: 'o',
            90: 'U',
            105: 'q',
            120: 'G',
            135: 'Q',
            150: 'H',
            165: 'W',
            180: 'L',
            195: 'x',
            210: 'N',
            225: 'Z',
            240: 'F',
            255: 'V',
            270: 'D',
            285: 'Y',
            300: 'B',
            315: 'C',
            330: 'M',
            345: 'J',
            999: '!'
        }
        angleData = pd.Series(self.__dict__['angleData'])
        pathData = list(angleData.map(mapping))
        self.__dict__.pop('angleData')
        ret = ''
        for i in pathData:
            ret += i
        self.__dict__['pathData'] = ret

    def pathDataToAngleData(self):
        # 同上个方法
        mapping = {
            'R': 0,
            'p': 15,
            'J': 30,
            'E': 45,
            'T': 60,
            'o': 75,
            'U': 90,
            'q': 105,
            'G': 120,
            'Q': 135,
            'H': 150,
            'W': 165,
            'L': 180,
            'x': 195,
            'N': 210,
            'Z': 225,
            'F': 240,
            'V': 255,
            'D': 270,
            'Y': 285,
            'B': 300,
            'C': 315,
            'M': 330,
            'A': 345,
            '!': 999
        }
        self.__dict__['pathData'] = list(self.__dict__['pathData'])
        pathData = pd.Series(self.__dict__['pathData'])
        angleData = list(pathData.map(mapping))
        self.__dict__.pop('pathData')
        self.__dict__['angleData'] = angleData

    def save(self):
        # adofai().save()
        # 保存adofai文件
        file = self.__dict__
        path = self.path

        with open(path, 'w+', encoding='utf-8') as f:
            # 先把self转成字典dump进去，变成字符串好处理
            json.dump(file, f, indent=4)
        with open(path, 'r', encoding='utf-8') as f:
            # 不能用w模式，否则直接清空，读到的是空白，r和w必须分开
            file = f.read()
        with open(path, 'w', encoding='utf-8') as f:
            # 去除无用的东西
            file = re.sub('"path":.*?,', '', file)
            file = re.sub('" "', '""', file)
            f.write(file)

    def removeEvents(self,args={}):
        #adofai().removeEvents( {参数:值} )
        #去除符合条件的事件
        #示例:removeEvents({'floor':100})去除第100格的事件

        actions = copy.deepcopy(self.actions)
        keys = list(args.keys())
        for action in range(len(actions)):
            conform = 0
            for i in keys:
                if actions[action][i] == args[i]:
                    conform+=1
                if conform == len(keys):
                    self.actions.pop(action)
