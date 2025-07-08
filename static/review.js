// Toggle topics
function toggleTopic(clickedHeader) {
    const clickedTopic = clickedHeader.parentElement;
    const clickedMaterials = clickedTopic.querySelector('.materials');
    const isOpen = clickedTopic.classList.contains('open');

    document.querySelectorAll('.topic').forEach(topic => {
        const materials = topic.querySelector('.materials');

        if (topic !== clickedTopic && topic.classList.contains('open')) {
            // Closing animation
            materials.style.height = materials.scrollHeight + 'px';
            requestAnimationFrame(() => {
                topic.classList.remove('open');
                materials.style.height = '0px';
            });
        }
    });

    if (isOpen) {
        // Close last material
        clickedMaterials.style.height = clickedMaterials.scrollHeight + 'px';
        requestAnimationFrame(() => {
            clickedTopic.classList.remove('open');
            clickedMaterials.style.height = '0px';
        });
    } else {
        // Open current material
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

    desc.style.maxHeight = desc.scrollHeight + 'px';

    setTimeout(() => {
    desc.style.opacity = '1';
    desc.style.pointerEvents = 'auto';
    }, 150);
}

function hideDesc(material) {
    const desc = material.querySelector('.material-desc');

    desc.style.opacity = '0';
    desc.style.pointerEvents = 'none';

    setTimeout(() => {
    desc.style.maxHeight = '0';
    }, 300);
}