<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Kiusumu Mpya Bus Park</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Montserrat:wght@600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* --- Reset & Base --- */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Roboto', sans-serif; background-color: #f4f6f8; color: #333; overflow-x: hidden; }
        a { text-decoration: none; }

        /* --- Header / Navbar --- */
        header { background: linear-gradient(135deg, #1a73e8, #34a853); color: white; padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        header h1 { font-family: 'Montserrat', sans-serif; font-size: 28px; }
        nav a { margin-left: 20px; font-weight: 600; color: white; transition: 0.3s; }
        nav a:hover { color: #fbbc05; }

        /* --- Animated Hero Section --- */
        .hero { position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90vh; text-align: center; color: white; overflow: hidden; }

        /* Moving Gradient Background */
        .gradient-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(270deg, #1a73e8, #34a853, #fbbc05, #ea4335); background-size: 800% 800%; animation: gradientMove 20s ease infinite; z-index: 0; }
        @keyframes gradientMove { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

        /* Floating Shapes */
        .shape { position: absolute; border-radius: 50%; opacity: 0.3; animation: floatShape 20s linear infinite; }
        .shape:nth-child(1) { width: 80px; height: 80px; background: #fbbc05; top: 10%; left: 20%; animation-duration: 12s; }
        .shape:nth-child(2) { width: 50px; height: 50px; background: #ea4335; top: 50%; left: 10%; animation-duration: 18s; }
        .shape:nth-child(3) { width: 100px; height: 100px; background: #34a853; top: 30%; left: 70%; animation-duration: 22s; }
        .shape:nth-child(4) { width: 60px; height: 60px; background: #1a73e8; top: 70%; left: 50%; animation-duration: 16s; }
        @keyframes floatShape { 0% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-60px) rotate(180deg); } 100% { transform: translateY(0) rotate(360deg); } }

        /* Particle Canvas (WebGL-style) */
        .particle-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; }

        /* Hero Content */
        .hero-content { position: relative; z-index: 2; animation: fadeUp 1.5s ease forwards; }
        @keyframes fadeUp { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
        .hero h2 { font-size: 48px; margin-bottom: 20px; text-shadow: 2px 2px 8px rgba(0,0,0,0.5); }
        .hero p { font-size: 20px; margin-bottom: 30px; max-width: 600px; }
        .hero .btn { background-color: #fbbc05; color: #1a73e8; padding: 12px 28px; border-radius: 8px; font-weight: bold; transition: 0.3s; margin: 0 8px; }
        .hero .btn:hover { background-color: #fff; color: #1a73e8; }

        /* --- Features Section --- */
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 30px; padding: 60px 40px; text-align: center; }
        .feature-card { background: white; padding: 30px 20px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.08); transition: transform 0.3s, box-shadow 0.3s; opacity: 0; transform: translateY(20px); animation: fadeIn 1s forwards; }
        .feature-card:nth-child(1) { animation-delay: 0.2s; }
        .feature-card:nth-child(2) { animation-delay: 0.4s; }
        .feature-card:nth-child(3) { animation-delay: 0.6s; }
        .feature-card:nth-child(4) { animation-delay: 0.8s; }
        .feature-card:hover { transform: translateY(-8px); box-shadow: 0 12px 25px rgba(0,0,0,0.12); }
        .feature-card h3 { margin-bottom: 12px; color: #1a73e8; }
        .feature-card p { font-size: 15px; color: #555; }
        @keyframes fadeIn { to { opacity: 1; transform: translateY(0); } }

        /* --- Footer with Social Icons --- */
        footer { background: #1a73e8; color: white; padding: 30px 40px; text-align: center; font-size: 14px; }
        .social-icons { margin-top: 10px; }
        .social-icons a { color: white; margin: 0 10px; font-size: 22px; transition: 0.3s; }
        .social-icons a:hover { color: #fbbc05; }

        /* --- Responsive --- */
        @media(max-width: 768px) {
            .hero h2 { font-size: 36px; }
            .hero p { font-size: 16px; }
        }
    </style>
</head>
<body>
    <!-- Header / Navbar -->
    <header>
        <h1>Kiusumu Mpya Bus Park</h1>
        <nav>
            <a href="/bus_entry">Bus Entry</a>
            <a href="/bus_exit">Bus Exit</a>
            <a href="/reports">Reports</a>
        </nav>
    </header>
    
    <!-- Hero Section -->
    <section class="hero">
        <div class="gradient-bg"></div>
        <div class="shape"></div>
        <div class="shape"></div>
        <div class="shape"></div>
        <div class="shape"></div>
        <canvas class="particle-canvas"></canvas>

        <div class="hero-content">
            <h2>Seamless Bus Management in Kisumu</h2>
            <p>Track bus entries, manage parking slots, calculate fees, and generate reports — all in one place.</p>
            <a href="/bus_entry" class="btn">Enter a Bus</a>
            <a href="/bus_exit" class="btn">Exit a Bus</a>
        </div>
    </section>
    
    <!-- Features / Presentation Body -->
    <section class="features">
        <div class="feature-card">
            <h3>Real-time Tracking</h3>
            <p>Monitor all bus entries and exits instantly to improve efficiency and reduce delays.</p>
        </div>
        <div class="feature-card">
            <h3>Smart Parking</h3>
            <p>Automatically assign and track available parking slots for a smooth flow of buses.</p>
        </div>
        <div class="feature-card">
            <h3>Reports & Analytics</h3>
            <p>Generate detailed reports to understand traffic trends and optimize operations.</p>
        </div>
        <div class="feature-card">
            <h3>Secure & Reliable</h3>
            <p>Keep all records safe, accurate, and accessible only to authorized personnel.</p>
        </div>
    </section>
    
    <!-- Footer -->
    <footer>
        <p>Designed by <a href="#">Daose David</a> | &copy; 2026 Kiusumu Mpya Bus Park</p>
        <div class="social-icons">
            <a href="https://wa.me/254123456789" target="_blank" rel="noreferrer"><i class="fab fa-whatsapp"></i></a>
            <a href="mailto:info@kiusumupark.com"><i class="fas fa-envelope"></i></a>
            <a href="tel:+254123456789"><i class="fas fa-phone"></i></a>
        </div>
    </footer>

    <script>
        // Particle effect (WebGL-style moving dots)
        const canvas = document.querySelector('.particle-canvas');
        const ctx = canvas.getContext('2d');
        const particles = [];
        const particleCount = 80;

        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = document.querySelector('.hero').offsetHeight;
        }

        function randomBetween(min, max) { return Math.random() * (max - min) + min; }

        function createParticles() {
            particles.length = 0;
            for (let i = 0; i < particleCount; i++) {
                particles.push({
                    x: randomBetween(0, canvas.width),
                    y: randomBetween(0, canvas.height),
                    radius: randomBetween(1.5, 3.5),
                    speed: randomBetween(0.15, 0.5),
                    angle: randomBetween(0, Math.PI * 2),
                    alpha: randomBetween(0.15, 0.55),
                });
            }
        }

        function drawParticles() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach((p) => {
                p.x += Math.cos(p.angle) * p.speed;
                p.y += Math.sin(p.angle) * p.speed;
                p.angle += 0.002;

                if (p.x < -20) p.x = canvas.width + 20;
                if (p.x > canvas.width + 20) p.x = -20;
                if (p.y < -20) p.y = canvas.height + 20;
                if (p.y > canvas.height + 20) p.y = -20;

                const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius * 2);
                gradient.addColorStop(0, `rgba(255,255,255,${p.alpha})`);
                gradient.addColorStop(1, 'rgba(255,255,255,0)');

                ctx.beginPath();
                ctx.fillStyle = gradient;
                ctx.arc(p.x, p.y, p.radius * 2, 0, Math.PI * 2);
                ctx.fill();
            });
        }

        function animate() {
            drawParticles();
            requestAnimationFrame(animate);
        }

        function updateHeroParallax() {
            const hero = document.querySelector('.hero');
            const content = hero.querySelector('.hero-content');
            const offset = window.scrollY * 0.15;
            content.style.transform = `translateY(${offset}px)`;
        }

        window.addEventListener('resize', () => {
            resizeCanvas();
            createParticles();
        });

        window.addEventListener('scroll', updateHeroParallax);

        resizeCanvas();
        createParticles();
        animate();
    </script>
</body>
</html>