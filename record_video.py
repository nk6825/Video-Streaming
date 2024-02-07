import cv2

def main():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Failed to open camera.")
    else:
        flag = 0
        packet_number = 1
        while True:
            ret, frame = camera.read()

            if not ret:
                print("INFO: No more frames in stream. Exiting...")
                break
            else:
                if flag == 0:
                    frame_in_bytes = cv2.imencode(".jpg", frame)[1].tobytes()
                    
                    fragment_number = 1
                    frame_length = len(frame_in_bytes)

                    fragment_number = 2
                    fragment_in_bytes_list = bytearray()
                    while len(frame_in_bytes) != 0:
                        fragment_in_bytes = frame_in_bytes[:4084]
                        fragment_in_bytes_list = bytearray(list(fragment_in_bytes))
                        
                        fragment_in_bytes_list.clear()
                        frame_in_bytes = frame_in_bytes[4084:]
                        fragment_number += 1

                    if packet_number == 200:
                        packet_number = 1
                    else:
                        packet_number += 1

                    flag = 1
                cv2.imshow("frame", frame)

            if cv2.waitKey(1) == ord("q"):
                break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
