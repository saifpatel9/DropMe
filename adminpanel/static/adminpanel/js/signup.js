document.addEventListener('DOMContentLoaded', function() {
    // Toggle switch functionality
    const toggleStatus = () => {
        const toggle = document.getElementById('statusToggle');
        const statusText = document.getElementById('statusText');
        const statusInput = document.getElementById('id_status');
        
        if (toggle.classList.contains('active')) {
            toggle.classList.remove('active');
            statusText.textContent = 'Inactive';
            statusInput.value = 'inactive';
        } else {
            toggle.classList.add('active');
            statusText.textContent = 'Active';
            statusInput.value = 'active';
        }
    };

    // Initialize toggle based on current value
    const statusInput = document.getElementById('id_status');
    if (statusInput && statusInput.value === 'active') {
        document.getElementById('statusToggle').classList.add('active');
        document.getElementById('statusText').textContent = 'Active';
    }

    // Add click event to toggle switch
    const toggleElement = document.getElementById('statusToggle');
    if (toggleElement) {
        toggleElement.addEventListener('click', toggleStatus);
    }

    // Payment option selection
    document.querySelectorAll('.payment-option').forEach(option => {
        option.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                // Add active class to selected option
                document.querySelectorAll('.payment-option').forEach(opt => {
                    opt.classList.remove('active');
                });
                this.classList.add('active');
            }
        });
    });

    // Initialize payment option active state
    const checkedPayment = document.querySelector('.payment-option input[type="radio"]:checked');
    if (checkedPayment) {
        checkedPayment.closest('.payment-option').classList.add('active');
    }
});