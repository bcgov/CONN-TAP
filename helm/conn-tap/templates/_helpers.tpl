{{- define "conn-tap.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "conn-tap.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "conn-tap.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "conn-tap.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "conn-tap.selectorLabels" -}}
app.kubernetes.io/name: {{ include "conn-tap.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "conn-tap.backendName" -}}
{{- printf "%s-backend" (include "conn-tap.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "conn-tap.frontendName" -}}
{{- printf "%s-frontend" (include "conn-tap.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "conn-tap.backendSecretName" -}}
{{- default (include "conn-tap.backendName" .) .Values.backend.existingSecret -}}
{{- end -}}

{{- define "conn-tap.frontendSecretName" -}}
{{- default (include "conn-tap.frontendName" .) .Values.frontend.existingSecret -}}
{{- end -}}
