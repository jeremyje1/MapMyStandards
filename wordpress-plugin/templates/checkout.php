<?php
/**
 * A³E Checkout Template for WordPress
 */
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checkout - A³E | <?php bloginfo('name'); ?></title>
    
    <!-- Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Stripe.js -->
    <script src="https://js.stripe.com/v3/"></script>
    
    <!-- WordPress Head -->
    <?php wp_head(); ?>
    
    <style>
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: #f9fafb;
            margin: 0;
            padding: 0;
        }
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .container { max-width: 64rem; margin: 0 auto; padding: 0 1rem; }
        .header { background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-bottom: 1px solid #e5e7eb; }
        .header-content { display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; }
        .main-content { max-width: 64rem; margin: 0 auto; padding: 3rem 1rem; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
        .card { background: white; border-radius: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 2rem; }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Include the checkout content from the HTML file -->
    <?php
    // Get the checkout HTML content
    $checkout_html = file_get_contents(dirname(__FILE__) . '/../../web/checkout.html');
    
    // Extract just the body content (between <body> and </body>)
    preg_match('/<body[^>]*>(.*?)<\/body>/s', $checkout_html, $matches);
    if (isset($matches[1])) {
        echo $matches[1];
    }
    ?>
    
    <?php wp_footer(); ?>
</body>
</html>
