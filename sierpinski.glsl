
precision mediump float;

uniform vec2 u_resolution;
uniform float u_time;

float random1(vec2 st) {
    return fract(sin(dot(st.xy,
                         vec2(12.9898,78.233)))*43758.5453123);
}

float random(vec2 st) {
    return random1(st);
    float r1 = random1(st.xy);
    float r2 = random1(st.yx);
    return random1(vec2(r1, r2));
}

vec2 random_element(vec2[3] v, float r) {
    if (r < 1.0/3.0) {
        return v[0];
    } else if (r < 2.0/3.0) {
        return v[1];
    } else {
        return v[2];
    }
}

void main()
{
    vec2 uv = gl_FragCoord.xy/u_resolution.xy;
    vec3 col = 0.5 + 0.5*cos(u_time+uv.xyx+vec3(0,2,4));

    vec2 ps[3];
    ps[0] = vec2(0, 0);
    ps[1] = vec2(1, 0);
    ps[2] = vec2(0, 1);

    float color_total = 0.0;

    vec2 point = vec2(0.8, 0.5);
    for (float i = 0.0; i < 100.0; i++) {
        vec2 point2 = random_element(ps, random(u_resolution.xy*col.xy*(i + 50.0)));
        point = (point + point2) / 2.0;

        if (i > 20.0 && distance(uv, point) < 0.01) {
            color_total += 1.0;
        }
    }

    if (color_total > 0.0) {
        gl_FragColor = vec4(1);
    } else {
        gl_FragColor = vec4(0);
    }
}
