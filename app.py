from flask import Flask, render_template, request, redirect, session, Response
import psycopg2
import cv2
import numpy as np

app = Flask(__name__)
app.secret_key = "secretkey123"
blur_background = False

# =========================
# POSTGRESQL CONNECTION
# =========================
conn = psycopg2.connect(
    host="localhost",
    database="surveillance_db",
    user="postgres",
    password="admin123",
    port="5432"
)

cursor = conn.cursor()

# =========================
# CAMERA SETUP
# =========================
# 0 = local webcam
# Replace with RTSP link later if needed
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Warning: Camera not available")


# =========================
# VIDEO STREAM FUNCTION
# =========================
def generate_frames():

    global blur_background

    while True:

        success, frame = camera.read()

        if not success:
            break

        # Create blurred version
        blurred_frame = cv2.GaussianBlur(
            frame,
            (55, 55),
            0
        )

        # Convert to grayscale
        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        # Apply blur mode
        if blur_background:

            # Start with blurred frame
            output_frame = blurred_frame.copy()

            # Restore original face area
            for (x, y, w, h) in faces:

                output_frame[y:y+h, x:x+w] = frame[y:y+h, x:x+w]

                cv2.rectangle(
                    output_frame,
                    (x, y),
                    (x+w, y+h),
                    (0, 255, 0),
                    2
                )

        else:

            output_frame = frame.copy()

            for (x, y, w, h) in faces:

                cv2.rectangle(
                    output_frame,
                    (x, y),
                    (x+w, y+h),
                    (0, 255, 0),
                    2
                )

        # Convert frame to JPEG
        ret, buffer = cv2.imencode('.jpg', output_frame)

        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame +
            b'\r\n'
        )

# =========================
# LOGIN ROUTE
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )

        user = cursor.fetchone()

        if user:

            session['user'] = username

            # SAVE LOGIN LOG
            cursor.execute(
                "INSERT INTO login_logs (username) VALUES (%s)",
                (username,)
            )

            conn.commit()

            return redirect('/')

        else:

            return render_template(
                'login.html',
                error="Invalid username or password"
            )

    return render_template('login.html')


# =========================
# REGISTER ROUTE
# =========================
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return render_template(
                'register.html',
                error="Username already exists"
            )

        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )

        conn.commit()

        return redirect('/login')

    return render_template('register.html')


# =========================
# DASHBOARD
# =========================
@app.route('/')
def dashboard():

    # Protect dashboard
    if 'user' not in session:
        return redirect('/login')

    try:
        cursor.execute(
            "SELECT * FROM camera_logs ORDER BY id DESC"
        )

        logs = cursor.fetchall()

    except psycopg2.Error as e:

        print("Database error:", e)

        logs = []

    return render_template(
        'dashboard.html',
        logs=logs,
        user=session['user']
    )


# =========================
# VIDEO STREAM ROUTE
# =========================
@app.route('/video')
def video():

    if 'user' not in session:
        return redirect('/login')

    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# =========================
# LOGOUT ROUTE
# =========================
@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/login')

# =========================
# CAMERA MONITORING ROUTE
# =========================
@app.route('/camera_monitoring')
def camera_monitoring():

    # Protect page
    if 'user' not in session:
        return redirect('/login')

    return render_template(
        'camera_monitoring.html',
        user=session['user']
    )


# =========================
# DEVICE MANAGEMENT ROUTE
# =========================
@app.route('/device_management')
def device_management():

    # Protect page
    if 'user' not in session:
        return redirect('/login')

    devices = [

        {
            "name": "Router",
            "ip": "192.168.1.1",
            "status": "ONLINE"
        },

        {
            "name": "IP Camera",
            "ip": "192.168.1.10",
            "status": "ONLINE"
        },

        {
            "name": "Web Server",
            "ip": "192.168.1.20",
            "status": "ONLINE"
        }

    ]

    return render_template(
        'device_management.html',
        devices=devices,
        user=session['user']
    )


# =========================
# FACE DETECTION
# =========================
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    'haarcascade_frontalface_default.xml'
)

# =========================
# LOGIN LOGS PAGE
# =========================
@app.route('/login_logs')
def login_logs():

    if 'user' not in session:
        return redirect('/login')

    cursor.execute(
        "SELECT * FROM login_logs ORDER BY login_time DESC"
    )

    logs = cursor.fetchall()

    return render_template(
        'login_logs.html',
        logs=logs,
        user=session['user']
    )

# =========================
# TOGGLE BLUR BACKGROUND
# =========================
@app.route('/toggle_blur')
def toggle_blur():

    global blur_background

    blur_background = not blur_background

    return redirect('/camera_monitoring')

# =========================
# RUN APP
# =========================
if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )