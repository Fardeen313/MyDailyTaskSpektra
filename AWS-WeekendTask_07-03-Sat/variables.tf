variable "image" {
  type        = string
  description = "amazon linux 2023"
  default     = ""
}
variable "key" {
  type        = string
  description = ""
  default     = ""
}
variable "instance_type" {
  type        = string
  description = ""
  default     = ""
}
variable "bucket" {
  description = "s3_buckeet_name"
  type        = string
  default     = ""
}
variable "bucket_key" {
  type        = string
  description = "directory_inside_bucket"
  default     = ""
}