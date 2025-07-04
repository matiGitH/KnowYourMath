function toggleTopic(clickedHeader) {
    const clickedTopic = clickedHeader.parentElement;
    const clickedMaterials = clickedTopic.querySelector('.materials');
    const isOpen = clickedTopic.classList.contains('open');

    // Cerrar todos los demás
    document.querySelectorAll('.topic').forEach(topic => {
        const materials = topic.querySelector('.materials');

        if (topic !== clickedTopic && topic.classList.contains('open')) {
            // Animación de cierre
            materials.style.height = materials.scrollHeight + 'px';
            requestAnimationFrame(() => {
                topic.classList.remove('open');
                materials.style.height = '0px';
            });
        }
    });

    if (isOpen) {
        // Cerrar el actual
        clickedMaterials.style.height = clickedMaterials.scrollHeight + 'px';
        requestAnimationFrame(() => {
            clickedTopic.classList.remove('open');
            clickedMaterials.style.height = '0px';
        });
    } else {
        // Abrir el actual
        clickedTopic.classList.add('open');
        clickedMaterials.style.height = clickedMaterials.scrollHeight + 'px';
        clickedMaterials.addEventListener('transitionend', () => {
            if (clickedTopic.classList.contains('open')) {
                clickedMaterials.style.height = 'auto';
            }
        }, { once: true });
    }
}


function showDesc(material) {
    const desc = material.querySelector('.material-desc');

    // Fase 1: set max-height dinámico
    desc.style.maxHeight = desc.scrollHeight + 'px';

    // Fase 2: luego de un delay, activamos opacidad
    setTimeout(() => {
    desc.style.opacity = '1';
    desc.style.pointerEvents = 'auto';
    }, 150);
}

function hideDesc(material) {
    const desc = material.querySelector('.material-desc');

    // Fase 1: ocultar opacidad
    desc.style.opacity = '0';
    desc.style.pointerEvents = 'none';

    // Fase 2: luego de fade out, colapsamos altura
    setTimeout(() => {
    desc.style.maxHeight = '0';
    }, 300); // coincidir con transition-duration de opacity
}