<?php
/**
 * Plugin Name: A³E SaaS Integration
 * Description: Integrates A³E checkout and dashboard into WordPress
 * Version: 1.0.0
 * Author: MapMyStandards.ai
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class A3E_SaaS_Integration {
    
    public function __construct() {
        add_action('init', array($this, 'init'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));
        add_filter('template_include', array($this, 'template_include'));
    }
    
    public function init() {
        // Add rewrite rules for checkout and dashboard
        add_rewrite_rule('^checkout/?$', 'index.php?a3e_page=checkout', 'top');
        add_rewrite_rule('^dashboard/?$', 'index.php?a3e_page=dashboard', 'top');
        
        // Add query vars
        add_filter('query_vars', function($vars) {
            $vars[] = 'a3e_page';
            return $vars;
        });
        
        // Flush rewrite rules on activation
        if (get_option('a3e_flush_rewrite_rules')) {
            flush_rewrite_rules();
            delete_option('a3e_flush_rewrite_rules');
        }
    }
    
    public function enqueue_scripts() {
        if (is_a3e_page()) {
            // Enqueue Tailwind CSS
            wp_enqueue_script('tailwind-css', 'https://cdn.tailwindcss.com', array(), '3.0.0');
            
            // Enqueue Stripe.js
            wp_enqueue_script('stripe-js', 'https://js.stripe.com/v3/', array(), '3.0.0');
            
            // Enqueue Inter font
            wp_enqueue_style('inter-font', 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        }
    }
    
    public function template_include($template) {
        $a3e_page = get_query_var('a3e_page');
        
        if ($a3e_page === 'checkout') {
            return $this->load_checkout_template();
        } elseif ($a3e_page === 'dashboard') {
            return $this->load_dashboard_template();
        }
        
        return $template;
    }
    
    private function load_checkout_template() {
        // Include the checkout.html content
        $checkout_file = plugin_dir_path(__FILE__) . 'templates/checkout.php';
        if (file_exists($checkout_file)) {
            return $checkout_file;
        }
        return get_404_template();
    }
    
    private function load_dashboard_template() {
        // Include the dashboard.html content
        $dashboard_file = plugin_dir_path(__FILE__) . 'templates/dashboard.php';
        if (file_exists($dashboard_file)) {
            return $dashboard_file;
        }
        return get_404_template();
    }
}

// Helper function
function is_a3e_page() {
    return get_query_var('a3e_page') !== '';
}

// Initialize the plugin
new A3E_SaaS_Integration();

// Activation hook
register_activation_hook(__FILE__, function() {
    add_option('a3e_flush_rewrite_rules', true);
});
?>
