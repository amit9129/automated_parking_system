# camera_integration.py
import cv2
import pytesseract

# Set the path to your Tesseract installation (only necessary on Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def read_number_plate(frame):
    # Preprocess the image (convert to grayscale, blur, etc.)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Use edge detection to find contours
    edged = cv2.Canny(blurred, 100, 200)

    # Find contours in the edged image
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Loop over the contours
    for contour in contours:
        # Approximate the contour
        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)

        # Assuming the license plate is a rectangle (4 points)
        if len(approx) == 4:
            # Get the bounding box of the detected contour
            x, y, w, h = cv2.boundingRect(approx)
            plate_img = frame[y:y + h, x:x + w]

            # Use Tesseract to do OCR on the license plate region
            number_plate = pytesseract.image_to_string(plate_img, config='--psm 8')  # --psm 8 treats the image as a single block of text
            return number_plate.strip()  # Return the recognized number plate

    return None  # If no plate was found

def capture_image():
    camera = cv2.VideoCapture(0)  # Use your camera index
    ret, frame = camera.read()
    if ret:
        number_plate = read_number_plate(frame)
        camera.release()  # Release the camera
        return number_plate
    camera.release()  # Release the camera
    return None  # If unable to capture

if __name__ == "__main__":
    plate = capture_image()
    print(f"Captured Number Plate: {plate}")
