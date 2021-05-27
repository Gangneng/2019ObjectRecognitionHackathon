import tello_c as  tello
import time
import cv2
import Dec


def runTello(movepoint=False,x=0,y=0,z=0):
    SecurityLevel = 3
    ObjConstSize = [2217, 2217, 330, 555, 7300]
    Load_dec = Dec.Inference()
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter("output.avi", fourcc, 25.0, (640, 480))
    logBuffer = []

    def log(logStr):
        logStr = logStr.strip()

        logBuffer.append(logStr)
        print(len(logBuffer), ":", logStr)

    def stateReceive(stateData):
        print("receive_state:", stateData)
        return None

    drone = tello.Tello(log, stateReceive)
    drone.local_main_ip = '192.168.10.3'
    drone.local_main_port = 8889

    if not drone.tryConnect():
        print("연결실패")
        exit()

    time = 0
    fflag = 0
    # cap=cv2.VideoCapture(0)
    while True:

        frame = drone.readFrame();
        # _,frame=cap.read()

        if frame is not None:  ##이미지 들어오면 영상처리 ㄱㄱ
            # cv2.imshow("test",frame)
            if movepoint:
                movepoint=False
                drone.send_command("goto %d %d %d 100"%(x,y,z))
            fflag += 1
            if fflag <= 4:
                continue
            fflag = 0
            objInfo, dst = Load_dec.infer(frame)

            if len(objInfo) > 0:
                for i in range(len(objInfo)):
                    if objInfo[i]['label'] == "wild_boar":
                        objInfo[i]['label'] = 0
                    elif objInfo[i]['label'] == "Cervidae":
                        objInfo[i]['label'] = 1
                    elif objInfo[i]['label'] == "bird":
                        objInfo[i]['label'] = 2
                    elif objInfo[i]['label'] == "Person":
                        objInfo[i]['label'] = 3
                    else:
                        objInfo[i]['label'] = 4
                for i in range(len(objInfo) - 1):
                    for j in range(i, len(objInfo)):
                        if objInfo[i]['label'] > objInfo[j]['label']:
                            objInfo[i]['label'], objInfo[j]['label'] = objInfo[j]['label'], objInfo[i]['label']

                TrObj = objInfo[0]
                if TrObj['label'] < SecurityLevel:
                    Xmin, Xmax, Ymin, Ymax = TrObj['xmin'], TrObj['xmax'], TrObj['ymin'], TrObj['ymax'];
                    X = (Xmin + Xmax) // 2
                    Y = (Ymin + Ymax) // 2
                    cv2.circle(dst, (X, Y), radius=10, color=(0, 255, 0), thickness=-1)
                    width = frame.shape[1] // 2
                    mvy = (Y - width) / width * 30
                    if (mvy >= 0):
                        drone.send_command("cw %d" % int(mvy))
                    else:
                        drone.send_command("ccw %d" % abs(int(mvy)))
                    if (abs(mvy) < 10):
                        drone.send_command("forward 20")
                    if (X < frame.shape[0] // 2):
                        drone.send_command("up 30")
                    else:
                        drone.send_command("down 30")

            cv2.imshow("cvt", dst)
            out.write(dst)

            k = cv2.waitKey(1)
            if k != 0 and k != -1:
                print("key", k)
            if k == ord('t'):
                drone.send_command("takeoff");
            if k == ord('a'):
                drone.send_command("ccw 15")
            if k == ord('w'):
                drone.send_command("forward 30")
            if k == ord('d'):
                drone.send_command("cw 15")
            if k == 27:
                drone.send_command("land")
                drone.disconnect();
                out.release()
                break;

    cv2.destroyAllWindows()



