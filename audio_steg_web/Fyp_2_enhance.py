import wave
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Function to convert a character to its custom binary representation
def char_to_custom_binary(char):
    if char.isdigit():  # Numbers (0-9)
        marker = '0'
        binary_val = f"{int(char):04b}"  # 4-bit binary for numbers
        return marker + binary_val
    elif char.isupper():  # Uppercase letters (A-Z)
        marker = '10'
        binary_val = f"{ord(char) - ord('A'):05b}"  # 5-bit binary for A-Z
        return marker + binary_val
    elif char.islower():  # Lowercase letters (a-z)
        marker = '11'
        binary_val = f"{ord(char) - ord('a'):05b}"  # 5-bit binary for a-z
        return marker + binary_val
    else:
        raise ValueError(f"Unsupported character: {char}")

# Function to convert custom binary back to a character
def custom_binary_to_char(binary):
    if binary.startswith('0'):  # Numbers
        number = int(binary[1:], 2)  # Convert last 4 bits to decimal
        return str(number)
    elif binary.startswith('10'):  # Uppercase letters
        letter = chr(int(binary[2:], 2) + ord('A'))  # Convert last 5 bits
        return letter
    elif binary.startswith('11'):  # Lowercase letters
        letter = chr(int(binary[2:], 2) + ord('a'))  # Convert last 5 bits
        return letter
    else:
        raise ValueError(f"Unsupported binary sequence: {binary}")

# Function to embed the secret message in the WAV file using LSB
def embed_message(audio_file, output_file, secret_message):
    with wave.open(audio_file, 'rb') as audio:
        params = audio.getparams()
        frames = bytearray(list(audio.readframes(audio.getnframes())))

    # Convert secret message to binary
    binary_message = ''.join(char_to_custom_binary(char) for char in secret_message)
    binary_message += '11111111'  # Add EOF marker

    # Check if message can fit
    if len(binary_message) > len(frames):
        raise ValueError("Message is too large to hide in this audio file.")

    # Embed the binary message into the least significant bits
    for i, bit in enumerate(binary_message):
        frames[i] = (frames[i] & 254) | int(bit)  # Set LSB to the current bit

    # Save the modified frames to a new audio file
    with wave.open(output_file, 'wb') as audio_out:
        audio_out.setparams(params)
        audio_out.writeframes(bytes(frames))

# Function to extract the secret message from the WAV file
def extract_message(stego_file):
    with wave.open(stego_file, 'rb') as audio:
        frames = list(audio.readframes(audio.getnframes()))

    # Extract the LSBs to reconstruct the binary message
    binary_message = ''.join(str(frame & 1) for frame in frames)

    # Read characters until the EOF marker is found
    decoded_message = []
    i = 0
    while i < len(binary_message):
        if binary_message[i:i+8] == '11111111':  # EOF marker
            break
        if binary_message[i] == '0':  # Numbers
            decoded_message.append(custom_binary_to_char(binary_message[i:i+5]))
            i += 5
        elif binary_message[i:i+2] == '10':  # Uppercase letters
            decoded_message.append(custom_binary_to_char(binary_message[i:i+7]))
            i += 7
        elif binary_message[i:i+2] == '11':  # Lowercase letters
            decoded_message.append(custom_binary_to_char(binary_message[i:i+7]))
            i += 7
        else:
            raise ValueError(f"Invalid binary sequence starting at index {i}")

    return ''.join(decoded_message)

# GUI Application

def main():
    def browse_audio():
        path = filedialog.askopenfilename(title="Select WAV File", filetypes=[("WAV files", "*.wav")])
        if path:
            selected_audio.set(path)

    def encode():
        audio_path = selected_audio.get()
        if not audio_path:
            messagebox.showerror("Error", "Please select a WAV file.")
            return

        text = text_input.get("1.0", "end-1c")
        if not text:
            messagebox.showerror("Error", "Please enter text to encode.")
            return

        output_path = filedialog.asksaveasfilename(title="Save Stego File", defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
        if not output_path:
            return

        try:
            embed_message(audio_path, output_path, text)
            messagebox.showinfo("Success", "Text successfully encoded into audio!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def decode():
        audio_path = filedialog.askopenfilename(title="Select Stego WAV File", filetypes=[("WAV files", "*.wav")])
        if not audio_path:
            return

        try:
            decoded_text = extract_message(audio_path)
            text_output.delete("1.0", "end")
            text_output.insert("1.0", decoded_text)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    root = tk.Tk()
    root.title("Audio Steganography")
    root.geometry("700x500")
    root.resizable(False, False)

    selected_audio = tk.StringVar()

    # ========== Input Frame ==========
    input_frame = ttk.LabelFrame(root, text="1. Encode Message")
    input_frame.pack(fill="x", padx=10, pady=10)

    ttk.Label(input_frame, text="Secret Message:").pack(anchor="w", padx=10, pady=(10, 0))
    text_input = tk.Text(input_frame, height=5)
    text_input.pack(fill="x", padx=10, pady=5)

    ttk.Button(input_frame, text="Browse WAV File", command=browse_audio).pack(pady=5)
    ttk.Label(input_frame, textvariable=selected_audio, foreground="gray").pack(pady=2)

    ttk.Button(input_frame, text="Embed Message", command=encode).pack(pady=10)

    # ========== Output Frame ==========
    output_frame = ttk.LabelFrame(root, text="2. Decode Message (Steganalysis)")
    output_frame.pack(fill="x", padx=10, pady=10)

    ttk.Button(output_frame, text="Select WAV File to Decode", command=decode).pack(pady=5)

    ttk.Label(output_frame, text="Extracted Message:").pack(anchor="w", padx=10, pady=(10, 0))
    text_output = tk.Text(output_frame, height=5)
    text_output.pack(fill="x", padx=10, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
