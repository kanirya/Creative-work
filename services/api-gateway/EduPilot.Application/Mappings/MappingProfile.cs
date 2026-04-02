using AutoMapper;
using EduPilot.Application.DTOs;
using EduPilot.Domain.Entities;

namespace EduPilot.Application.Mappings;

public class MappingProfile : Profile
{
    public MappingProfile()
    {
        // Student mappings
        CreateMap<Student, StudentDto>()
            .ForMember(dest => dest.Email, opt => opt.MapFrom(src => src.Email.Value))
            .ForMember(dest => dest.UniversityId, opt => opt.MapFrom(src => src.UniversityId.Value))
            .ForMember(dest => dest.FullName, opt => opt.MapFrom(src => src.FullName));

        // Course mappings
        CreateMap<Course, CourseDto>()
            .ForMember(dest => dest.Code, opt => opt.MapFrom(src => src.Code.Value));

        // Assignment mappings
        CreateMap<Assignment, AssignmentDto>()
            .ForMember(dest => dest.Grade, opt => opt.MapFrom(src => src.Grade != null ? src.Grade.ToString() : null))
            .ForMember(dest => dest.IsOverdue, opt => opt.MapFrom(src => src.IsOverdue));

        // Announcement mappings
        CreateMap<Announcement, AnnouncementDto>();

        // Lecture Recording mappings
        CreateMap<LectureRecording, LectureRecordingDto>()
            .ForMember(dest => dest.HasTranscription, opt => opt.MapFrom(src => src.HasTranscription));
    }
}
