// Main JavaScript for the self-service system

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    // Add to cart functionality
    $('.add-to-cart-btn').on('click', function(e) {
        e.preventDefault();
        var $btn = $(this);
        var productId = $btn.data('product-id');
        var quantity = $btn.data('quantity') || 1;
        
        // Show loading state
        $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status"></span> Adicionando...');
        
        $.ajax({
            url: '/cart/add/',
            method: 'POST',
            data: {
                'product_id': productId,
                'quantity': quantity,
                'csrfmiddlewaretoken': getCookie('csrftoken')
            },
            success: function(response) {
                if (response.success) {
                    // Show success message
                    showToast(response.message, 'success');
                    
                    // Update cart counter
                    updateCartCounter(response.cart_total);
                    
                    // Update button state
                    $btn.removeClass('btn-primary').addClass('btn-success').html('<i class="bi bi-check"></i> Adicionado!');
                    
                    // Reset button after 2 seconds
                    setTimeout(function() {
                        $btn.removeClass('btn-success').addClass('btn-primary').html('<i class="bi bi-cart-plus"></i> Adicionar');
                        $btn.prop('disabled', false);
                    }, 2000);
                } else {
                    showToast(response.error, 'error');
                    $btn.prop('disabled', false).html('<i class="bi bi-cart-plus"></i> Adicionar');
                }
            },
            error: function() {
                showToast('Erro ao adicionar produto ao carrinho.', 'error');
                $btn.prop('disabled', false).html('<i class="bi bi-cart-plus"></i> Adicionar');
            }
        });
    });

    // Remove from cart functionality
    $('.remove-from-cart-btn').on('click', function(e) {
        e.preventDefault();
        var $btn = $(this);
        var productId = $btn.data('product-id');
        var $cartItem = $btn.closest('.cart-item');
        
        if (confirm('Tem certeza que deseja remover este produto do carrinho?')) {
            $.ajax({
                url: '/cart/remove/',
                method: 'POST',
                data: {
                    'product_id': productId,
                    'csrfmiddlewaretoken': getCookie('csrftoken')
                },
                success: function(response) {
                    if (response.success) {
                        // Remove item from DOM
                        $cartItem.fadeOut(300, function() {
                            $(this).remove();
                            
                            // Update cart totals
                            updateCartTotals(response.cart_total, response.cart_amount);
                            
                            // Check if cart is empty
                            if (response.cart_total == 0) {
                                location.reload();
                            }
                        });
                        
                        showToast(response.message, 'success');
                    } else {
                        showToast(response.error, 'error');
                    }
                },
                error: function() {
                    showToast('Erro ao remover produto do carrinho.', 'error');
                }
            });
        }
    });

    // Update cart quantity
    $('.update-quantity-btn').on('click', function(e) {
        e.preventDefault();
        var $btn = $(this);
        var productId = $btn.data('product-id');
        var $quantityInput = $btn.siblings('.quantity-input');
        var quantity = parseInt($quantityInput.val());
        
        if (quantity < 1) {
            showToast('Quantidade deve ser pelo menos 1.', 'error');
            return;
        }
        
        $.ajax({
            url: '/cart/update/',
            method: 'POST',
            data: {
                'product_id': productId,
                'quantity': quantity,
                'csrfmiddlewaretoken': getCookie('csrftoken')
            },
            success: function(response) {
                if (response.success) {
                    // Update item subtotal
                    $btn.closest('.cart-item').find('.item-subtotal').text('R$ ' + response.item_subtotal);
                    
                    // Update cart totals
                    updateCartTotals(response.cart_total, response.cart_amount);
                    
                    showToast(response.message, 'success');
                } else {
                    showToast(response.error, 'error');
                    // Reset quantity input
                    $quantityInput.val($quantityInput.data('original-value'));
                }
            },
            error: function() {
                showToast('Erro ao atualizar quantidade.', 'error');
                // Reset quantity input
                $quantityInput.val($quantityInput.data('original-value'));
            }
        });
    });

    // Quantity input change
    $('.quantity-input').on('change', function() {
        var $input = $(this);
        var $updateBtn = $input.siblings('.update-quantity-btn');
        
        // Show update button
        $updateBtn.show();
        
        // Store original value
        if (!$input.data('original-value')) {
            $input.data('original-value', $input.val());
        }
    });

    // Search functionality
    var searchTimeout;
    $('#search-input').on('input', function() {
        var query = $(this).val();
        var $searchResults = $('#search-results');
        
        // Clear previous timeout
        clearTimeout(searchTimeout);
        
        if (query.length < 2) {
            $searchResults.hide();
            return;
        }
        
        // Set new timeout
        searchTimeout = setTimeout(function() {
            $.ajax({
                url: '/products/api/search-suggestions/',
                method: 'GET',
                data: { 'q': query },
                success: function(response) {
                    if (response.suggestions && response.suggestions.length > 0) {
                        var html = '';
                        response.suggestions.forEach(function(item) {
                            html += `
                                <div class="search-suggestion-item p-2 border-bottom" data-url="${item.url}">
                                    <div class="d-flex align-items-center">
                                        <img src="${item.image || '/static/img/no-image.png'}" 
                                             class="me-2" style="width: 40px; height: 40px; object-fit: cover;">
                                        <div class="flex-grow-1">
                                            <div class="fw-bold">${item.name}</div>
                                            <small class="text-muted">R$ ${item.price}</small>
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                        
                        $searchResults.html(html).show();
                    } else {
                        $searchResults.hide();
                    }
                },
                error: function() {
                    $searchResults.hide();
                }
            });
        }, 300); // 300ms delay
    });

    // Click on search suggestion
    $(document).on('click', '.search-suggestion-item', function() {
        var url = $(this).data('url');
        window.location.href = url;
    });

    // Hide search results when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('#search-input, #search-results').length) {
            $('#search-results').hide();
        }
    });

    // Order cancellation
    $('.cancel-order-btn').on('click', function(e) {
        e.preventDefault();
        var $btn = $(this);
        var orderNumber = $btn.data('order-number');
        
        if (confirm('Tem certeza que deseja cancelar este pedido?')) {
            $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status"></span> Cancelando...');
            
            $.ajax({
                url: '/orders/cancel/' + orderNumber + '/',
                method: 'POST',
                data: {
                    'csrfmiddlewaretoken': getCookie('csrftoken')
                },
                success: function(response) {
                    if (response.success) {
                        showToast(response.message, 'success');
                        
                        // Update order status display
                        $btn.closest('.order-item').find('.order-status').text(response.new_status);
                        
                        // Remove cancel button
                        $btn.remove();
                        
                        // Reload page after 2 seconds
                        setTimeout(function() {
                            location.reload();
                        }, 2000);
                    } else {
                        showToast(response.error, 'error');
                        $btn.prop('disabled', false).html('Cancelar Pedido');
                    }
                },
                error: function() {
                    showToast('Erro ao cancelar pedido.', 'error');
                    $btn.prop('disabled', false).html('Cancelar Pedido');
                }
            });
        }
    });

    // Product review submission
    $('#review-form').on('submit', function(e) {
        e.preventDefault();
        var $form = $(this);
        var productSlug = $form.data('product-slug');
        
        $.ajax({
            url: '/products/api/submit-review/' + productSlug + '/',
            method: 'POST',
            data: $form.serialize(),
            success: function(response) {
                if (response.success) {
                    showToast(response.message, 'success');
                    $form[0].reset();
                    
                    // Reload reviews section
                    setTimeout(function() {
                        location.reload();
                    }, 1500);
                } else {
                    showToast(response.error, 'error');
                }
            },
            error: function() {
                showToast('Erro ao enviar avaliação.', 'error');
            }
        });
    });

    // Filter form submission
    $('#filter-form').on('submit', function(e) {
        e.preventDefault();
        
        // Get filter values
        var minPrice = $('#min-price').val();
        var maxPrice = $('#max-price').val();
        var brand = $('#brand-filter').val();
        var sort = $('#sort-select').val();
        
        // Build URL parameters
        var params = new URLSearchParams();
        
        if (minPrice) params.append('min_price', minPrice);
        if (maxPrice) params.append('max_price', maxPrice);
        if (brand) params.append('brand', brand);
        if (sort) params.append('sort', sort);
        
        // Redirect to filtered results
        window.location.href = window.location.pathname + '?' + params.toString();
    });

    // Price range slider (if using noUiSlider or similar)
    if ($('#price-range').length) {
        // Initialize price range slider here if needed
    }

    // Image lazy loading
    if ('IntersectionObserver' in window) {
        var imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    var img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(function(img) {
            imageObserver.observe(img);
        });
    }

    // Loading states for AJAX requests
    $(document).ajaxStart(function() {
        $('body').addClass('loading');
    }).ajaxStop(function() {
        $('body').removeClass('loading');
    });
});

// Utility functions
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showToast(message, type = 'info') {
    // Create toast element
    var toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'primary'} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Add toast container if it doesn't exist
    if (!$('#toast-container').length) {
        $('body').append('<div id="toast-container" class="toast-container position-fixed bottom-0 end-0 p-3"></div>');
    }
    
    // Append toast and show it
    var $toast = $(toastHtml).appendTo('#toast-container');
    var toast = new bootstrap.Toast($toast[0]);
    toast.show();
    
    // Remove toast element after it's hidden
    $toast.on('hidden.bs.toast', function() {
        $(this).remove();
    });
}

function updateCartCounter(total) {
    var $badge = $('.navbar .badge');
    if (total > 0) {
        $badge.text(total).show();
    } else {
        $badge.hide();
    }
}

function updateCartTotals(totalItems, totalAmount) {
    $('.cart-total-items').text(totalItems);
    $('.cart-total-amount').text('R$ ' + totalAmount);
}

// Quantity input controls
$(document).on('click', '.quantity-minus', function() {
    var $input = $(this).siblings('.quantity-input');
    var currentValue = parseInt($input.val());
    if (currentValue > 1) {
        $input.val(currentValue - 1).trigger('change');
    }
});

$(document).on('click', '.quantity-plus', function() {
    var $input = $(this).siblings('.quantity-input');
    var currentValue = parseInt($input.val());
    var max = parseInt($input.attr('max')) || 999;
    if (currentValue < max) {
        $input.val(currentValue + 1).trigger('change');
    }
});

// Prevent form submission on Enter key in search input
$(document).on('keypress', '#search-input', function(e) {
    if (e.which === 13) {
        e.preventDefault();
        $(this).closest('form').submit();
    }
});