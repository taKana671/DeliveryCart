#version 300 es
precision highp float;

uniform float tex_ScaleFactor0;
uniform float tex_ScaleFactor1;
uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;

in vec2 texcoord0;
in vec2 texcoord1;

in vec4 vertex;
out vec4 fragColor;

float computeWeight(float min_z, float max_z, vec4 vertex){
    float region = max_z - min_z;
    return max(0.0, (region - abs(vertex.z - max_z)) / region);
}

void main() {
    vec4 tex0 = texture(p3d_Texture0, texcoord0.st * tex_ScaleFactor0).rgba;
    vec4 tex1 = texture(p3d_Texture1, texcoord1.st * tex_ScaleFactor1).rgba;

    float scale = 300.0;
    float min_z = 0.0;
    float max_z = 0.0;

    min_z = -100.0/scale;
    max_z = 35.0/scale;
    float w0 = computeWeight(min_z, max_z, vertex);
    float w = clamp(w0 * 2.0, 0.0, 1.0);

    vec3 color = vec3(0.0);
    color += pow(tex0.rgb, vec3(2.2)) * w;
    color += pow(tex1.rgb, vec3(2.2)) * (1.0 - w);

    fragColor.rgb = color;
    fragColor.rgb = pow(fragColor.rgb, vec3(1.0 / 2.2));
}

