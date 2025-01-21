from flask import Flask, render_template_string, render_template, request, jsonify
import numpy as np
import plotly.graph_objects as go

app = Flask(__name__)

# Predefined platform points
base_points = {
    0: (-0.14, -0.13),
    1: (-0.19, -0.06),
    2: (-0.04, 0.195),
    3: (0.04, 0.195),
    4: (0.19, -0.06),
    5: (0.14, -0.13)
}

top_points = {
    0: (-0.04, -0.19),
    1: (-0.19, 0.060),
    2: (-0.14, 0.134),
    3: (0.14, 0.134),
    4: (0.19, 0.060),
    5: (0.04, -0.19)
}

# Extract coordinates
base_x = [p[0] for p in base_points.values()]
base_y = [p[1] for p in base_points.values()]
base_z = [0] * len(base_x)  # Base height is 0

top_x = [p[0] for p in top_points.values()]
top_y = [p[1] for p in top_points.values()]
top_z = [5] * len(top_x)  # Default top height is 5

# Function to create a 3D Stewart Platform plot
def create_stewart_platform(offset_x=0, offset_y=0, offset_z=0, rotation=0, actuator_height=5):
    # Adjust the height of the top platform
    adjusted_top_z = [z + actuator_height - 5 for z in top_z]  # Adjust height of actuators
    
    # Apply offsets and rotation to the top platform
    rotation_matrix = np.array([
        [np.cos(rotation), -np.sin(rotation), 0],
        [np.sin(rotation), np.cos(rotation), 0],
        [0, 0, 1],
    ])
    top_points_rotated = np.dot(
        rotation_matrix,
        np.vstack((top_x, top_y, np.array(adjusted_top_z) + offset_z))
    )
    top_points_rotated[0] += offset_x
    top_points_rotated[1] += offset_y

    # Create the figure
    fig = go.Figure()

    # Add the base platform
    fig.add_trace(go.Mesh3d(
        x=base_x,
        y=base_y,
        z=base_z,
        color='black',
        opacity=0.5,
        flatshading=True,
        name='Base Platform'
    ))

    # Add the top platform
    fig.add_trace(go.Mesh3d(
        x=top_points_rotated[0],
        y=top_points_rotated[1],
        z=top_points_rotated[2],
        color='blue',
        opacity=0.5,
        flatshading=True,
        name='Top Platform'
    ))

    # Add actuators
    for i in range(6):
        fig.add_trace(go.Scatter3d(
            x=[base_x[i], top_points_rotated[0][i]],
            y=[base_y[i], top_points_rotated[1][i]],
            z=[base_z[i], top_points_rotated[2][i]],
            mode='lines',
            line=dict(color='red', width=4),
            name=f'Actuator {i + 1}',
        ))

    # Update layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-0.3, 0.3]),
            yaxis=dict(range=[-0.3, 0.3]),
            zaxis=dict(range=[-0.3, actuator_height + 1]),  # Adjust Z-axis range
        ),
        title="Custom Stewart Platform Simulation",
    )

    return fig


# Initial route / figure
@app.route('/')
def index():
    # Create the default plot
    fig = create_stewart_platform()
    plot_div = fig.to_html(full_html=False)
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stewart Platform</title>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    </head>
    <body>
        <h1>Custom Stewart Platform Simulation</h1>
        <form id="control-form">
            <label for="offset_x">Offset X:</label>
            <input type="number" id="offset_x" name="offset_x" step="0.01"><br>
            <label for="offset_y">Offset Y:</label>
            <input type="number" id="offset_y" name="offset_y" step="0.01"><br>
            <label for="offset_z">Offset Z:</label>
            <input type="number" id="offset_z" name="offset_z" step="0.01"><br>
            <label for="rotation">Rotation (radians):</label>
            <input type="number" id="rotation" name="rotation" step="0.01"><br>
            <label for="actuator_height">Actuator Height:</label>
            <input type="number" id="actuator_height" name="actuator_height" step="0.1" value="5"><br>
            <button type="button" id="update-btn">Update Plot</button>
        </form>
        <div id="plot-container">{{ plot_div|safe }}</div>

        <script>
            $(document).ready(function () {
                $('#update-btn').on('click', function () {
                    const formData = $('#control-form').serialize();
                    $.post('/update_plot', formData, function (response) {
                        $('#plot-container').html(response.plot_html);
                    }).fail(function () {
                        alert('Error updating the plot. Please check your inputs.');
                    });
                });
            });
        </script>
    </body>
    </html>
    """, plot_div=plot_div)


@app.route('/update_plot', methods=['POST'])
def update_plot():
    try:
        offset_x = float(request.form.get('offset_x', 0))
        offset_y = float(request.form.get('offset_y', 0))
        offset_z = float(request.form.get('offset_z', 0))
        rotation = float(request.form.get('rotation', 0))
        actuator_height = float(request.form.get('actuator_height', 5))  # New field

        # Create the updated plot
        fig = create_stewart_platform(offset_x, offset_y, offset_z, rotation, actuator_height)
        fig_html = fig.to_html(full_html=False)

        return jsonify({'plot_html': fig_html})
    except ValueError:
        return jsonify({'error': 'Invalid input values'}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
