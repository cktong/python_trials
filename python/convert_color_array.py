from PIL import Image
import numpy as np
import json
import requests
import io
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.cm import ScalarMappable

class AutoColormap:
    def __init__(self, rgb_colors):
        self.rgb_colors = rgb_colors
        self.rgb_array = np.array(rgb_colors) / 255.0
        self.num_colors = len(rgb_colors)

    def to_magnitude(self, rgb_value):
        # Find the index of the closest RGB color
        idx = np.argmin(np.linalg.norm(self.rgb_array - (rgb_value / 255.0), axis=1))
        # Return the corresponding magnitude
        return idx + 1  # Assigning magnitudes starting from 1

with open("extracted_colors.json", "r") as file:
    extracted_colors = json.load(file)
extracted_colors.reverse()

# Convert RGB array to Matplotlib colormap
cmap = ListedColormap(np.array(extracted_colors) / 255.0)

url = "http://www.weather.gov.sg/files/rainarea/50km/v2/dpsri_70km_2024052514000000dBR.dpsri.png"
response = requests.get(url)

if response.status_code == 200:
    image_bytes = response.content
else:
    print("Failed to fetch data:", response.status_code)
# Convert PNG image to numpy array
image_b = np.array(image_bytes)
# Convert the image bytes to a PIL Image object
image = Image.open(io.BytesIO(image_bytes))
# Convert image to numpy array
rain_data = np.array(image)
print(rain_data[1])
# Map rain data to colormap

# # Create a ScalarMappable object with the colormap and normalization
# sm = ScalarMappable(cmap=cmap, norm=Normalize(vmin=0, vmax=len(extracted_colors) - 1))

# # Get the scalar values corresponding to each color in the colormap
# rain_values = np.linspace(0, len(extracted_colors) - 1, len(extracted_colors))

auto_cmap = AutoColormap(extracted_colors)
# Iterate over each pixel in the rain data and map RGB values to rain values
for i in range(rain_data.shape[0]):
  for j in range(rain_data.shape[1]):
      rgb_value = rain_data[i, j]
      print(rgb_value)
      magnitude = auto_cmap.to_magnitude(rgb_value)
      # scalar_value = np.argmax(np.all(rgb_value == np.array(extracted_colors), axis=1))
      # rain_value = rain_values[scalar_value]
      print(f"Pixel ({i}, {j}): Rain Value: {magnitude}")

# Plot the colormap and display the scalar values on the colorbar
plt.figure(figsize=(8, 6))
plt.imshow(rain_data, cmap=cmap, aspect='auto')
plt.colorbar(label='Rain Magnitude')
plt.title('Rain Levels')
plt.show()
plt.savefig('rain_magnitude_plot.png')

