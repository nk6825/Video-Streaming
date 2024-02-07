import sys
import pyaudio
import socket
import threading
import time
import cv2


CHUNK = 506
FORMAT = pyaudio.paInt16
CHANNELS = 1 
RATE = 44100
RECORD_SECONDS = 20
RTP_LENGTH_TABLE = dict()
RTP_FRAGMENT_TABLE = dict()
THREAD_TERMINATE_FLAG = 0

def get_encoded_rtp(rtp_payload, packet_number=0, fragment_number=0):
    rtp_packet = bytearray()
    rtp_header = bytearray()

    rtp_version = "10"
    rtp_padding = "0"
    rtp_extension = "0"
    rtp_csrc_count = "0000"
    rtp_byte_1 = int(rtp_version + rtp_padding + rtp_extension + rtp_csrc_count, 2)
    rtp_header.append(rtp_byte_1)

    rtp_marker = "0"
    rtp_payload_type = "0001011"
    rtp_byte_2 = int(rtp_marker + rtp_payload_type, 2)
    rtp_header.append(rtp_byte_2)

    if packet_number == 0 and fragment_number == 0:
        rtp_byte_3 = 0
        rtp_byte_4 = 0
    else:
        rtp_byte_3 = packet_number
        rtp_byte_4 = fragment_number
    rtp_header.append(rtp_byte_3)
    rtp_header.append(rtp_byte_4)

    rtp_byte_5 = 0
    rtp_byte_6 = 0
    rtp_byte_7 = 0
    rtp_byte_8 = 0
    rtp_header.append(rtp_byte_5)
    rtp_header.append(rtp_byte_6)
    rtp_header.append(rtp_byte_7)
    rtp_header.append(rtp_byte_8)

    rtp_byte_9 = 1
    rtp_byte_10 = 1
    rtp_byte_11 = 1
    rtp_byte_12 = 1
    rtp_header.append(rtp_byte_9)
    rtp_header.append(rtp_byte_10)
    rtp_header.append(rtp_byte_11)
    rtp_header.append(rtp_byte_12)

    rtp_packet = rtp_header + bytearray(list(rtp_payload))

    return rtp_packet

def get_decoded_rtp(rtp_packet):
    rtp_packet = list(rtp_packet)

    packet_number = int.from_bytes(rtp_packet[2:3], "big")
    fragment_number = int.from_bytes(rtp_packet[3:4], "big")
    rtp_payload = rtp_packet[12:]

    if packet_number != 0 and fragment_number != 0:
        if fragment_number == 1:
            RTP_LENGTH_TABLE[packet_number] = rtp_payload.decode()
        else:
            if packet_number not in RTP_FRAGMENT_TABLE:
                RTP_FRAGMENT_TABLE[packet_number] = bytearray()

            if fragment_number not in RTP_FRAGMENT_TABLE[packet_number]:
                RTP_FRAGMENT_TABLE[packet_number][fragment_number] = bytearray()

            RTP_FRAGMENT_TABLE[packet_number][fragment_number] += bytearray(list(rtp_payload))
        
        return "success"
    else:
        return bytes(rtp_payload)

def receive_audio():
    UDP_IP = "196.168.100.101"
    UDP_PORT = 5004
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.bind((UDP_IP, UDP_PORT))

    pao = pyaudio.PyAudio()
    output_stream = pao.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)

    try:
        while True:
            data, address = my_socket.recvfrom(1024)
            output_stream.write(get_decoded_rtp(data))
    except:
        print("ERROR: Exception detected.")
    finally:
        print("INFO: Releasing resources...")
        my_socket.close()
        output_stream.close()
        pao.terminate()

def send_audio():
    mic = pyaudio.PyAudio()
    input_stream = mic.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True)

    UDP_IP = "192.168.100.104"
    UDP_PORT = 5004
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        print("INFO: Recording in progress...")
        for i in range(0, RATE // CHUNK * RECORD_SECONDS):
            read_data = input_stream.read(CHUNK)
            encoded_data = get_encoded_rtp(read_data)
            my_socket.sendto(encoded_data, (UDP_IP, UDP_PORT))
        print("INFO: Recording complete.")
    except:
        print("ERROR: Exception detected.")
    finally:
        print("INFO: Releasing Resources...")
        input_stream.close()
        mic.terminate()
        my_socket.close()

def draw_video_frames():
    current_frame = 1
    while True:
        if THREAD_TERMINATE_FLAG:
            sys.exit()
        else:
            if len(RTP_LENGTH_TABLE) == 0:
                time.sleep(1)
            else:
                if current_frame in RTP_LENGTH_TABLE and current_frame in RTP_FRAGMENT_TABLE:
                    current_frame_length = 0
                    
                    for fragment in RTP_FRAGMENT_TABLE[current_frame]:
                        current_frame_length += RTP_FRAGMENT_TABLE[current_frame][fragment]

                    if current_frame_length == RTP_LENGTH_TABLE[current_frame]:
                        sorted_fragments = dict(sorted(RTP_FRAGMENT_TABLE[current_frame].items()))                      

                        print(sorted_fragments)

                        if current_frame == 200:
                            current_frame = 1
                        else:
                            current_frame += 1
                    else:
                        time.sleep(1)

def receive_video():
    UDP_IP = "40.40.40.102"
    UDP_PORT = 5006
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.bind((UDP_IP, UDP_PORT))

    my_thread = threading.Thread(target=draw_video_frames(), args=())
    my_thread.start()

    try:
        while True:
            data, address = my_socket.recvfrom(4096)
            print(get_decoded_rtp)
    except:
        print("ERROR: Exception detected.")
    finally:
        print("INFO: Releasing resources...")
        THREAD_TERMINATE_FLAG = 1
        my_thread.join()
        my_socket.close()

def send_video():
    camera = cv2.VideoCapture(0)

    UDP_IP = "40.40.40.102"
    UDP_PORT = 5006
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
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
                        frame_length_in_bytes = frame_length.to_bytes((frame_length.bit_length() + 7) // 8, "big")
                        encoded_data = get_encoded_rtp(frame_length_in_bytes, packet_number, fragment_number)
                        my_socket.sendto(encoded_data, (UDP_IP, UDP_PORT))

                        fragment_number = 2
                        fragment_in_bytes_list = bytearray()
                        while len(frame_in_bytes) != 0:
                            fragment_in_bytes = frame_in_bytes[:4084]
                            encoded_data = get_encoded_rtp(fragment_in_bytes, packet_number, fragment_number)
                            my_socket.sendto(encoded_data, (UDP_IP, UDP_PORT))

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
    except:
        print("ERROR: Exception detected.")
    finally:
        print("INFO: Releasing resources...")
        camera.release()
        cv2.destroyAllWindows()
        my_socket.close()

def main():
    if len(sys.argv) == 2:
        option = int(sys.argv[1])

        if option == 0:
            receive_audio()
        elif option == 1:
            send_audio()
        elif option == 2:
            receive_video()
        elif option == 3:
            send_video()
        else:
            print("ERROR: Invalid input detected.")
    else:
        print("USAGE: python3 controller.py <1 for sender, 0 for receiver>")

if __name__ == "__main__":
    main()
