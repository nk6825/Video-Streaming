
import sys
import pyaudio

def main():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1 if sys.platform == 'darwin' else 2
    RATE = 44100
    RECORD_SECONDS = 5

    pai = pyaudio.PyAudio()
    input_stream = pai.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True)
    
    print("Recording in progress...")
    
    frames = []
    for i in range(0, RATE // CHUNK * RECORD_SECONDS):
        read_data = input_stream.read(1024)
        frames.append(read_data)

    print("Recording complete.")

    input_stream.close()
    pai.terminate()

    pao = pyaudio.PyAudio()

    print("Playing in progress...")

    output_stream = pao.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
    for frame in frames:
        output_stream.write(frame)

    output_stream.close()
    pao.terminate()

    print("Playing complete.")

if __name__ == "__main__":
    main()
