function openEditModal() {
  const modal = document.getElementById("editProfileModal");
  if (modal) modal.classList.add("active");
}

function closeEditModal() {
  const modal = document.getElementById("editProfileModal");
  if (modal) modal.classList.remove("active");
}

// Encapsula inicialização para garantir que DOM e Cropper estejam disponíveis
function initProfileCropper() {
  // Fallback loader for CropperJS if CDN falhar
  let cropperLoadingPromise = null;
  function ensureCropperLoaded() {
    if (typeof Cropper !== "undefined") return Promise.resolve();
    if (cropperLoadingPromise) return cropperLoadingPromise;
    cropperLoadingPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js";
      script.onload = () => resolve();
      script.onerror = (err) => reject(err);
      document.head.appendChild(script);
    });
    return cropperLoadingPromise;
  }

  const modal = document.getElementById("editProfileModal");
  if (modal) {
    modal.addEventListener("click", function (e) {
      if (e.target === this) {
        closeEditModal();
      }
    });
  }

  let cropper;
  const imageInput = document.getElementById("profileImageInput");
  const imageToCrop = document.getElementById("imageToCrop");
  const cropperArea = document.getElementById("cropperArea");
  const imageUploadArea = document.getElementById("imageUploadArea");
  const form = document.getElementById("editProfileForm");
  const cancelBtn = document.getElementById("btnCropCancel");

  // Se algum elemento não existir, aborta silenciosamente (ex: página errada)
  if (!imageInput || !imageToCrop || !cropperArea || !imageUploadArea || !form) {
    return;
  }

  imageInput.addEventListener("change", function (e) {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      const reader = new FileReader();
      reader.onload = function (ev) {
        imageToCrop.src = ev.target.result;
        imageUploadArea.style.display = "none";
        cropperArea.style.display = "flex";

        if (cropper) {
          cropper.destroy();
        }

        ensureCropperLoaded()
          .then(() => {
            if (typeof Cropper !== "undefined") {
              cropper = new Cropper(imageToCrop, {
                aspectRatio: 1,
                viewMode: 1,
                minContainerWidth: 400,
                minContainerHeight: 300,
              });
            } else {
              console.error("CropperJS não carregado");
            }
          })
          .catch((err) => {
            console.error("Falha ao carregar CropperJS", err);
          });
      };
      reader.readAsDataURL(file);
    }
  });

  if (cancelBtn) {
    cancelBtn.addEventListener("click", function () {
      imageUploadArea.style.display = "flex";
      cropperArea.style.display = "none";
      imageInput.value = ""; // Clear input
      if (cropper) {
        cropper.destroy();
        cropper = null;
      }
    });
  }

  form.addEventListener("submit", function (e) {
    if (cropper) {
      e.preventDefault();
      cropper
        .getCroppedCanvas({
          width: 300,
          height: 300,
        })
        .toBlob((blob) => {
          const formData = new FormData(form);
          // Replace the file in FormData with the cropped blob
          formData.set("profile_image", blob, "profile.jpg");

          // Send via fetch
          fetch(form.action || window.location.href, {
            method: "POST",
            body: formData,
          })
            .then((response) => {
              if (response.ok) {
                window.location.reload();
              } else {
                alert("Erro ao atualizar perfil");
              }
            })
            .catch((err) => {
              console.error(err);
              alert("Erro ao atualizar perfil");
            });
        }, "image/jpeg");
    }
    // If no cropper (user didn't change image), let the form submit normally
  });
}

// Garante execução mesmo se DOMContentLoaded já tiver disparado
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initProfileCropper);
} else {
  initProfileCropper();
}
