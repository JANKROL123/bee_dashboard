import os
import cv2


def crop_images(
    input_folder,
    output_folder,
    x,
    y,
    width,
    height
):
    # Createing output folder
    os.makedirs(output_folder, exist_ok=True)

    # Available formats
    extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")

    # Image download
    files = sorted(
        f for f in os.listdir(input_folder)
        if f.lower().endswith(extensions)
    )

    print(f"{len(files)} images found.")

    for filename in files:

        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        image = cv2.imread(input_path)

        if image is None:
            print(f"[ERROR] Cannot read: {filename}")
            continue

        image_height, image_width = image.shape[:2]

        if image_width != 590 or image_height != 1895:
            print(
                f"[SKIP] {filename} - "
                f"nieprawidłowa rozdzielczość "
                f"({image_width}x{image_height})"
            )
            continue

        if (
            x < 0
            or y < 0
            or x + width > image_width
            or y + height > image_height
        ):
            print(
                f"[SKIP] {filename} - "
                f"crop wychodzi poza obraz"
            )
            continue

        cropped = image[
            y:y + height,
            x:x + width
        ]

        success = cv2.imwrite(output_path, cropped)

        if success:
            print(
                f"[OK] {filename} -> "
                f"{width}x{height}"
            )
        else:
            print(f"[ERROR] Nie można zapisać: {filename}")


if __name__ == "__main__":

    input_folder = "./images/private_source/priv_subset_2"
    output_folder = "./images/private_source/priv_subset_2/newpics"

    image_width = 590
    image_height = 1895

    # Left corner of clipped area
    x = 260
    y = 530

    # Clipped area size
    width = 325
    height = 1015

    crop_images(
        input_folder,
        output_folder,
        x,
        y,
        width,
        height
    )
    