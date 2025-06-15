
from flask import Flask, render_template, request, send_file
import wave
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def char_to_custom_binary(char):
    if char.isdigit():
        marker = '0'
        binary_val = f"{int(char):04b}"
        return marker + binary_val
    elif char.isupper():
        marker = '10'
        binary_val = f"{ord(char) - ord('A'):05b}"
        return marker + binary_val
    elif char.islower():
        marker = '11'
        binary_val = f"{ord(char) - ord('a'):05b}"
        return marker + binary_val
    else:
        raise ValueError(f"Unsupported character: {char}")

def custom_binary_to_char(binary):
    if binary.startswith('0'):
        number = int(binary[1:], 2)
        return str(number)
    elif binary.startswith('10'):
        letter = chr(int(binary[2:], 2) + ord('A'))
        return letter
    elif binary.startswith('11'):
        letter = chr(int(binary[2:], 2) + ord('a'))
        return letter
    else:
        raise ValueError(f"Unsupported binary sequence: {binary}")

def embed_message(audio_file, output_file, secret_message):
    with wave.open(audio_file, 'rb') as audio:
        params = audio.getparams()
        frames = bytearray(list(audio.readframes(audio.getnframes())))

    binary_message = ''.join(char_to_custom_binary(char) for char in secret_message)
    binary_message += '11111111'

    if len(binary_message) > len(frames):
        raise ValueError("Message is too large to hide in this audio file.")

    for i, bit in enumerate(binary_message):
        frames[i] = (frames[i] & 254) | int(bit)

    with wave.open(output_file, 'wb') as audio_out:
        audio_out.setparams(params)
        audio_out.writeframes(bytes(frames))

def extract_message(stego_file):
    with wave.open(stego_file, 'rb') as audio:
        frames = list(audio.readframes(audio.getnframes()))

    binary_message = ''.join(str(frame & 1) for frame in frames)

    decoded_message = []
    i = 0
    while i < len(binary_message):
        if binary_message[i:i+8] == '11111111':
            break
        if binary_message[i] == '0':
            decoded_message.append(custom_binary_to_char(binary_message[i:i+5]))
            i += 5
        elif binary_message[i:i+2] == '10':
            decoded_message.append(custom_binary_to_char(binary_message[i:i+7]))
            i += 7
        elif binary_message[i:i+2] == '11':
            decoded_message.append(custom_binary_to_char(binary_message[i:i+7]))
            i += 7
        else:
            raise ValueError(f"Invalid binary sequence at index {i}")

    return ''.join(decoded_message)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    text = request.form['message']
    audio = request.files['audio']
    if not text or not audio:
        return "Error: Missing input.", 400

    audio_path = os.path.join(UPLOAD_FOLDER, secure_filename(audio.filename))
    audio.save(audio_path)
    output_name = request.form.get('output_name', 'stego_output').strip()
    if not output_name.endswith('.wav'):
    output_name += '.wav'
    output_path = os.path.join(UPLOAD_FOLDER, secure_filename(output_name))


    try:
        embed_message(audio_path, output_path, text)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/decode', methods=['POST'])
def decode():
    stego_audio = request.files['stego_audio']
    if not stego_audio:
        return "Error: No file uploaded.", 400

    audio_path = os.path.join(UPLOAD_FOLDER, secure_filename(stego_audio.filename))
    stego_audio.save(audio_path)

    try:
        message = extract_message(audio_path)
        return render_template("result.html", message=message)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)

