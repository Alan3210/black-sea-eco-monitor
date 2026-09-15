
export class CurrentParticleEngine {
  constructor({
    canvas,
    map,
    getField,
    particleCount = 1800,
  }) {
    this.canvas = canvas;
    this.map = map;
    this.getField = getField;
    this.particleCount = particleCount;
    this.ctx = canvas.getContext("2d");
    this.particles = [];
    this.running = false;
    this.frame = null;

    this.seed();
  }

  seed() {
    const width = this.canvas.clientWidth || 100;
    const height = this.canvas.clientHeight || 100;

    this.particles = Array.from(
      { length: this.particleCount },
      () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        age: Math.random() * 100,
        life: 100 + Math.random() * 200,
      }),
    );
  }

  resetParticle(particle) {
    particle.x =
      Math.random() * this.canvas.clientWidth;

    particle.y =
      Math.random() * this.canvas.clientHeight;

    particle.age = 0;
    particle.life =
      100 + Math.random() * 200;
  }

  pickVector(field) {
    if (!field?.vectors?.length) {
      return null;
    }

    return field.vectors[
      Math.floor(
        Math.random() * field.vectors.length,
      )
    ];
  }

  tick(delta) {
    const field = this.getField();

    if (!field?.vectors?.length) {
      return;
    }

    const ctx = this.ctx;

    ctx.fillStyle =
      "rgba(4,18,28,0.08)";

    ctx.fillRect(
      0,
      0,
      this.canvas.clientWidth,
      this.canvas.clientHeight,
    );

    for (const particle of this.particles) {
      const vector = this.pickVector(field);

      if (vector) {
        ctx.beginPath();
        ctx.moveTo(
          particle.x,
          particle.y,
        );

        particle.x += vector.u * delta * 0.25;
        particle.y -= vector.v * delta * 0.25;

        ctx.lineTo(
          particle.x,
          particle.y,
        );

        ctx.strokeStyle =
          "rgba(255,138,0,0.85)";

        ctx.lineWidth =
          1 + vector.speed * 3;

        ctx.stroke();
      }

      particle.age += 1;

      if (
        particle.age > particle.life
      ) {
        this.resetParticle(
          particle,
        );
      }
    }
  }

  start() {
    if (this.running) return;

    this.running = true;

    const loop = (time) => {
      if (!this.running) return;

      this.tick(16);

      this.frame =
        requestAnimationFrame(loop);
    };

    this.frame =
      requestAnimationFrame(loop);
  }

  stop() {
    this.running = false;

    if (this.frame) {
      cancelAnimationFrame(
        this.frame,
      );
    }
  }
}
