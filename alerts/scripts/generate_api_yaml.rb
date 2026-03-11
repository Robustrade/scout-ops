require 'net/http'
require 'json'
require 'yaml'
require 'fileutils'
require 'uri'
require 'set'

kong_admin = ENV['KONG_ADMIN_URL']

def fetch_routes(kong_admin)
  routes = []
  url = "#{kong_admin}/routes"

  loop do
    uri = URI(url)
    response = Net::HTTP.get_response(uri)
    raise "Failed to fetch routes" unless response.is_a?(Net::HTTPSuccess)

    body = JSON.parse(response.body)
    routes.concat(body["data"])

    break unless body["next"]
    url = "#{kong_admin}#{body["next"]}"
  end

  routes
end

routes = fetch_routes(kong_admin)

services = {}

routes.each do |route|
  tags = route["tags"] || []

  team = nil
  service_name = nil

  tags.each do |tag|
    if tag.start_with?("team=")
      team = tag.split("=")[1]
    elsif tag.end_with?("-gateway-backoffice-route")
      service_name = tag.sub("-gateway-backoffice-route", "")
    elsif tag.end_with?("-gateway-route")
      service_name = tag.sub("-gateway-route", "")
    elsif tag.end_with?("-public-route")
      service_name = tag.sub("-public-route", "")
    elsif tag.end_with?("-route")
      service_name = tag.sub("-route", "")
    end
  end

  if !team or !service_name
    puts "Missing team:#{team} or service_name: #{service_name} or tags: #{tags}"
    next
  end

  service_name = service_name.gsub("-", "_")

  api = {
    "name" => route["name"],
    "methods" => route["methods"] || [],
    "paths" => route["paths"] || [],
    "service" => { "name" => service_name },
    "tags" => { "team" => team }
  }

  key = "#{team}/#{service_name}"
  services[key] ||= []
  services[key] << api
end

services.each do |key, new_apis|
  team, service_name = key.split("/")

  dir = "specs/teams/#{team}/services/#{service_name}"
  FileUtils.mkdir_p(dir)

  file = "#{dir}/api.yaml"

  existing_apis = []

  if File.exist?(file)
    data = YAML.load_file(file)
    existing_apis = data["apis"] if data && data["apis"]
  end

  existing_names = existing_apis.map { |a| a["name"] }.to_set

  new_apis.each do |api|
    unless existing_names.include?(api["name"])
      existing_apis << api
      existing_names.add(api["name"])
    end
  end

  # keep deterministic order to avoid git noise
  existing_apis.sort_by! { |a| a["name"] }

  File.write(file, { "apis" => existing_apis }.to_yaml)
end

puts "Kong routes synced successfully without duplicates."
